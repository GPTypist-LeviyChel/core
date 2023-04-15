import random
import string

from src.common.result import Result
from src.entities.question import Question, QuestionType
from src.services.room import RoomService


class QuestionService:
    def __init__(self, room_service: RoomService):
        self._questions = {}
        self.room_service = room_service

    def init_room_questions(self, room_code: str, count: int):
        self._questions[room_code] = [Question(''.join(random.choices(string.ascii_uppercase + string.digits, k=10)),
                                               QuestionType.MULTIPLE_CHOICE, ['a', 'b', 'c', 'd'])
                                      for _ in range(count)]

    def next_question(self, room_code: str) -> Result:
        room = self.room_service.get_room(room_code)
        if room.is_error:
            return room

        room = room.value
        room.current_question += 1
        if room.current_question >= len(room.questions):
            return Result.ok('end')
        return Result.ok('continue')

    def get_question_count(self, room_code: str):
        return len(self._questions[room_code])
