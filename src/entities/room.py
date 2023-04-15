import secrets
from enum import IntEnum


class RoomStatus(IntEnum):
    PREPARATION = 0
    IN_PROGRESS = 1
    FINISHED = 2


class Room:
    def __init__(self, code: str):
        self.code = code
        self.users = {}
        self.status = RoomStatus.PREPARATION
        self.master_code = secrets.token_hex(16)
        self.current_question = -1
        self.questions = []
        self.current_answer = None
