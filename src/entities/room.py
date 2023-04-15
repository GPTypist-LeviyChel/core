import dataclasses
import secrets
from enum import IntEnum

from src.entities.question import Question
from src.entities.user import User


class RoomStatus(IntEnum):
    PREPARATION = 0
    IN_PROGRESS = 1
    FINISHED = 2


@dataclasses.dataclass
class Room:
    code: str
    master_token: str
    users: dict[str, User] = dataclasses.field(default_factory=lambda: {})
    status: RoomStatus = RoomStatus.PREPARATION
    current_question: int = -1
    questions: list[Question] = dataclasses.field(default_factory=lambda: [])
    current_answer: str | None = None
    questions_per_user: int = 1
    liked_by: set[str] = dataclasses.field(default_factory=lambda: set())
    disliked_by: set[str] = dataclasses.field(default_factory=lambda: set())
