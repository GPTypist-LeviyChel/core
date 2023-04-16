import random
import string
from dataclasses import asdict

from src.common.result import Result
from src.entities.room import Room, RoomStatus
from src.entities.user import User
from src.schema import make_event, EventType
from src.services.master import MasterVerifier
from src.services.token import TokenService
from src.session.conenctions import Connections


class RoomService:
    def __init__(self, token_service: TokenService, master_verify: MasterVerifier, connections: Connections):
        self.rooms: dict[str, Room] = {}
        self._codes = set()

        while len(self._codes) < 1000:
            self._codes.add(self._gen_room_code())

        self._codes = list(self._codes)
        random.shuffle(self._codes)

        self.token_service = token_service
        self.master_verify = master_verify
        self.connections = connections

    def _gen_room_code(self) -> str:
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

    @property
    def _bad_room(self) -> Result:
        return Result.error("Такой комнаты не сущетсвует")

    def _room_not_in_preparation(self, room_status: RoomStatus) -> Result | None:
        if room_status == RoomStatus.IN_PROGRESS:
            return Result.error("Игра уже началась")
        if room_status == RoomStatus.FINISHED:
            return Result.error("Игра уже закончилась")
        return None

    async def join_room(self, con_token: str, room_code: str, user_name: str, master_token: str = None) -> Result:
        room = self.rooms.get(room_code, None)
        if room is None:
            return self._bad_room

        wrong_status = self._room_not_in_preparation(room.status)
        if wrong_status:
            return wrong_status

        user_name = user_name.strip()

        if user_name in room.users:
            return Result.error("Такое име уже занято")

        if not user_name:
            return Result.error("Имя должно быть непустым")

        if any(not ch.isalnum() for ch in user_name):
            return Result.error("Такой ник нельзя")

        if len(user_name) > 100:
            return Result.error("Имя должно быть не длиннее 100 символов")

        room.users[user_name] = User(user_name, 'TODO', is_master=master_token is not None)
        token = master_token or self.token_service.create(user_name)
        self.connections.associate(con_token, (room.code, user_name))

        await self.connections.notify_all(room_code, user_name,
                                          make_event(EventType.USER_JOINED,
                                                     {"name": user_name, "profile_pic": 'TODO',
                                                      "is_master": False}))
        return Result.ok({"room": asdict(room), "user": asdict(room.users[user_name]), "token": token})

    async def leave_room(self, con_token: str) -> Result:
        room_code, user_name = self.connections.get_assoc(con_token) or ("", "")

        room = self.rooms.get(room_code, None)
        if room is None:
            return self._bad_room

        if user_name in room.users:
            room.users.pop(user_name)

        await self.connections.notify_all(room_code, user_name, make_event(EventType.USER_LEFT, {"name": user_name}))

        if not room.users:
            if room_code in self.rooms:
                self.rooms.pop(room_code)
                self._codes.append(room_code)
        elif room.users or user_name in room.users and room.users[user_name].is_master:
            return await self.end_room(room_code)

        return Result.ok()

    async def start_room(self, room_code: str, master_token: str) -> Result:
        room = self.rooms.get(room_code, None)
        if room is None:
            return self._bad_room

        wrong_status = self._room_not_in_preparation(room.status)
        if wrong_status:
            return wrong_status

        if room.master_token != master_token:
            return Result.error("Ошибка авторизации")

        room.status = RoomStatus.IN_PROGRESS

        await self.connections.notify_all(room_code, None, make_event(EventType.GAME_STARTED, {}))

        return Result.ok()

    async def create_room(self, con_token: str, master_name: str, questions_per_user: int) -> Result:
        if not self._codes:
            return Result.error("Пока нет свободных комнат")

        master_name = master_name.strip()
        if not master_name:
            return Result.error("Имя должно быть непустым")

        if questions_per_user < 1:
            return Result.error("Количество вопросов должно быть больше 0")

        code = self._codes[-1]
        master_token = self.token_service.create(master_name)
        room = Room(code, questions_per_user=questions_per_user, master_token=master_token)
        self.rooms[code] = room

        # 0 - master pic
        result = await self.join_room(con_token, code, master_name, master_token=master_token)
        if result.is_error:
            return result

        self.master_verify.set_master(code, master_token)
        self._codes.pop()
        random.shuffle(self._codes)

        self.connections.associate(con_token, (room.code, master_name))

        return result

    async def end_room(self, room_code: str) -> Result:
        room = self.get_room(room_code)
        if room.is_error:
            return room

        room = room.value

        self._codes.append(room.code)
        self.rooms.pop(room_code)
        random.shuffle(self._codes)

        await self.connections.notify_all(room_code, None, make_event(EventType.GAME_ENDED, {}))

        return Result.ok()

    def get_room(self, room_code: str) -> Result:
        room = self.rooms.get(room_code, None)
        if room is None:
            return self._bad_room

        return Result.ok(room)
