from enum import Enum, IntEnum

from pydantic import BaseModel

from src.entities.room import RoomStatus, Room


class CreateRoom(BaseModel):
    master_name: str
    questions_per_user: int


class StartRoom(BaseModel):
    room_code: str
    master_token: str


class JoinRoom(BaseModel):
    room_code: str
    user_name: str


class LeaveRoom(BaseModel):
    room_code: str
    user_name: str


class UserSchema(BaseModel):
    name: str
    profile_pic: str
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


class RoomUserToken(BaseModel):
    room: RoomSchema
    user: UserSchema
    token: str


class SubmitAnswer(BaseModel):
    room_code: str
    token: str
    answer: str


class LikeAnswer(BaseModel):
    room_code: str
    token: str


class NextQuestion(BaseModel):
    room_code: str
    token: str


class EventType(IntEnum):
    USER_JOINED = 1
    USER_LEFT = 2

    GAME_STARTED = 5
    GAME_ENDED = 6

    ANSWER_SUBMITTED = 8
    NEXT_QUESTION = 9

    LIKES_CHANGED = 11


def make_event(event_type: EventType, payload: dict):
    payload = payload.copy()
    payload['type'] = event_type
    return payload
