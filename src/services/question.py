import dataclasses
import random
import string

from src.common.result import Result
from src.entities.question import Question, QuestionType
from src.schema import make_event, EventType
from src.services.master import MasterVerifier
from src.services.room import RoomService
from src.services.token import TokenService
from src.session.conenctions import Connections


@dataclasses.dataclass
class Questions:
    questions: list[Question]


class QuestionService:
    def __init__(self, room_service: RoomService, token_service: TokenService, master_verify: MasterVerifier,
                 connections: Connections):
        self._orders = {}
        self.token_service = token_service
        self.room_service = room_service
        self.master_verify = master_verify
        self.connections = connections

    def init_room_questions(self, room_code: str, count: int):
        room = self.room_service.get_room(room_code)
        if room.is_error:
            return room

        room = room.value
        room.questions = [Question(''.join(random.choices(string.ascii_uppercase + string.digits, k=10)),
                                   QuestionType.MULTIPLE_CHOICE, ['a', 'b', 'c', 'd'])
                          for _ in range(count)]
        room.current_question = -1

        user_names = list(room.users.keys())
        random.shuffle(user_names)
        self._orders[room_code] = user_names

    def next_question(self, room_code: str, master_token: str) -> Result:
        if not self.master_verify.is_master(room_code, master_token):
            return Result.error("Invalid master token")

        room = self.room_service.get_room(room_code)
        if room.is_error:
            return room

        room = room.value
        room.current_question += 1
        if room.current_question >= len(room.questions):
            self.connections.notify_all(room_code, None, make_event(EventType.GAME_ENDED, {}))
            return Result.ok('end')

        question = room.questions[room.current_question]
        self.connections.notify_all(room_code, None, make_event(EventType.NEXT_QUESTION,
                                                                {'question': question, "question_type": question.type,
                                                                 "answers": question.answers,
                                                                 "answerer": self._orders[room_code][
                                                                     room.current_question]}))

        return Result.ok('continue')

    def submit_answer(self, room_code, token: str, answer: str):
        user_name = self.token_service.get_user(token)
        if user_name is None:
            return Result.error("Invalid token")

        answer = answer.strip()
        if not answer:
            return Result.error("Invalid answer")

        room = self.room_service.get_room(room_code)
        if room.is_error:
            return room

        room = room.value
        if user_name not in room.users:
            return Result.error('Invalid room')

        if room.current_answer is not None:
            return Result.error('Room already has an answer')

        room.current_answer = answer
        self.connections.notify_all(room_code, user_name, make_event(EventType.ANSWER_SUBMITTED, {"answer": answer}))

        return Result.ok()
