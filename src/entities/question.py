import dataclasses

from pydantic.validators import IntEnum


class QuestionType(IntEnum):
    MULTIPLE_CHOICE = 0
    SHORT_ANSWER = 1


@dataclasses.dataclass
class Question:
    question: str
    type: QuestionType
    image_url: str
    answers: list[str] | None = None
