from src.common.result import Result
from src.schema import make_event, EventType
from src.services.question import QuestionService
from src.services.room import RoomService
from src.session.conenctions import Connections


class AnswerService:
    def __init__(self, room_service: RoomService, question_server: QuestionService, connections: Connections):
        self.room_service = room_service
        self.question_service = question_server
        self.connections = connections

    def submit_answer(self, room_code, user_name: str, answer: str):
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
        self.connections.notify_all(user_name, make_event(EventType.ANSWER_SUBMITTED, {"answer": answer}))

        return Result.ok()
