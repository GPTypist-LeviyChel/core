from pydantic.validators import IntEnum


class QuestionType(IntEnum):
    MULTIPLE_CHOICE = 0
    SHORT_ANSWER = 1


class Question:
    def __init__(self, question: str, type: QuestionType, answers: list[str] = None):
        self.question = question
        self.type = type
        self.answers = answers
