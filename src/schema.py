from enum import Enum, IntEnum

from pydantic import BaseModel

from src.entities.room import RoomStatus, Room


class StartRoom(BaseModel):
    room_code: str
    master_code: str


class JoinRoom(BaseModel):
    room_code: str
    user_name: str
    profile_pic: int


class LeaveRoom(BaseModel):
    room_code: str
    user_name: str


class UserSchema(BaseModel):
    name: str
    profile_pic: int
    is_master: bool


class UserDict(dict[str, UserSchema]):
    pass


class UserList(BaseModel):
    users: list[UserSchema]


class RoomSchema(BaseModel):
    code: str
    users: dict[str, UserSchema]
    status: RoomStatus


class RoomMaster(RoomSchema):
    master_token: str


class UserToken(UserSchema):
    token: str


class RoomAndUserToken(BaseModel):
    room: RoomSchema
    user: UserToken


class SubmitAnswer(BaseModel):
    room_code: str
    token: str
    answer: str


class EventType(IntEnum):
    USER_JOINED = 1
    USER_LEFT = 2

    GAME_STARTED = 5
    GAME_ENDED = 6

    ANSWER_SUBMITTED = 8
    NEXT_QUESTION = 9


def make_event(event_type: EventType, payload: dict):
    payload = payload.copy()
    payload['type'] = event_type
    return payload
