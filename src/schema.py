from enum import Enum, IntEnum

from pydantic import BaseModel

from src.entities.room import RoomStatus


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
    pass
    # name: str
    # profile_pic: int
    # is_master: bool


class UserDict(BaseModel):
    users: dict[str, UserSchema]


class UserList(BaseModel):
    users: list[UserSchema]


class RoomSchema(BaseModel):
    room_code: str
    users: UserDict
    status: RoomStatus


class RoomMaster(RoomSchema):
    master_code: str


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
