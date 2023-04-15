import dataclasses
import random
import string
from dataclasses import asdict

from src.common.result import Result
from src.entities.room import Room, RoomStatus
from src.entities.user import User


class RoomService:
    def __init__(self):
        self.rooms: dict[str, Room] = {}
        self._codes = set()

        while len(self._codes) < 1000:
            self._codes.add(self._gen_room_code())

        self._codes = list(self._codes)
        random.shuffle(self._codes)

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

    def join_room(self, room_code: str, user_name: str, profile_pic: int, master_token: str = None) -> Result:
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

        # TODO: profile_pic

        if len(user_name) > 100:
            return Result.error("Имя должно быть не длиннее 100 символов")

        room.users[user_name] = User(user_name, profile_pic, master_token=master_token)
        return Result.ok({"room": asdict(room), "user": asdict(room.users[user_name])})

    def leave_room(self, room_code: str, user_name: str) -> Result:
        room = self.rooms.get(room_code, None)
        if room is None:
            return self._bad_room

        if user_name in room.users:
            room.users.pop(user_name)

        return Result.ok()

    def start_room(self, room_code: str, master_code: str) -> Result:
        room = self.rooms.get(room_code, None)
        if room is None:
            return self._bad_room

        wrong_status = self._room_not_in_preparation(room.status)
        if wrong_status:
            return wrong_status

        if room.master_code != master_code:
            return Result.error("Ошибка авторизации")

        room.status = RoomStatus.IN_PROGRESS
        return Result.ok()

    def create_room(self, master_name: str) -> Result:
        if not self._codes:
            return Result.error("Пока нет свободных комнат")

        code = self._codes[-1]
        code = 'AAAAAA'
        room = Room(code)
        self.rooms[code] = room

        # 0 - master pic
        result = self.join_room(code, master_name, 0, master_token=room.master_token)
        if result.is_error:
            return result

        self._codes.pop()

        return result

    def end_room(self, room_code: str) -> Result:
        room = self.rooms.get(room_code, None)
        if room is None:
            return self._bad_room

        self._codes.append(room.code)
        return Result.ok()

    def get_room(self, room_code: str) -> Result:
        room = self.rooms.get(room_code, None)
        if room is None:
            return self._bad_room

        return Result.ok(room)
