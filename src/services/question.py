import dataclasses
import random
import string
from urllib import request

import requests as requests

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

    def init_room_questions(self, room_code: str):
        room = self.room_service.get_room(room_code)
        if room.is_error:
            return room

        room = room.value
        try:
            response = requests.get(
                f'http://localhost:7040/api/v1/getQuestions/{(len(room.users) - 1) * room.questions_per_user}')
            body = response.json()
            room.questions = [Question(question=obj['text'], image_url=obj['image_url'], type=QuestionType.SHORT_ANSWER) for
                         obj in body]
        except:
            return Result.error("Cannot fetch questions")

        room.current_question = -1

        user_names = [k for k, v in room.users.items() if not v.is_master] * room.questions_per_user

        while True:
            random.shuffle(user_names)
            break
            # TODO:

            for i in range(1, len(user_names)):
                if user_names[i - 1] == user_names[i]:
                    break
            else:
                break

        self._orders[room_code] = user_names
        return Result.ok()

    async def next_question(self, room_code: str, master_token: str) -> Result:
        if not self.master_verify.is_master(room_code, master_token):
            return Result.error("Invalid master token")

        room = self.room_service.get_room(room_code)
        if room.is_error:
            return room

        room = room.value
        room.current_question += 1
        room.current_answer = None
        room.disliked_by.clear()
        room.liked_by.clear()

        if room.current_question >= len(room.questions):
            await self.connections.notify_all(room_code, None, make_event(EventType.GAME_ENDED, {}))
            return Result.ok()

        question = room.questions[room.current_question]
        await self.connections.notify_all(room_code, None, make_event(EventType.NEXT_QUESTION,
                                                                      {'question': question.question,
                                                                       "question_type": question.type,
                                                                       "image_url": question.image_url,
                                                                       "answers": question.answers,
                                                                       "answerer": self._orders[room_code][
                                                                           room.current_question]}))

        return Result.ok()

    async def submit_answer(self, room_code, token: str, answer: str):
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
        await self.connections.notify_all(room_code, user_name,
                                          make_event(EventType.ANSWER_SUBMITTED, {"answer": answer}))

        return Result.ok()

    async def start_game(self, room_code: str, master_token: str) -> Result:
        res = await self.room_service.start_room(room_code, master_token)
        if res.is_error:
            return res

        res = self.init_room_questions(room_code)
        if res.is_error:
            return res

        return await self.next_question(room_code, master_token)

    async def like_answer(self, room_code, token) -> Result:
        user_name = self.token_service.get_user(token)
        if user_name is None:
            return Result.error("Invalid token")

        room = self.room_service.get_room(room_code)
        if room.is_error:
            return room

        room = room.value
        if user_name not in room.users:
            return Result.error('Invalid room')

        if user_name in room.liked_by:
            return Result.error('Already liked')

        room.liked_by.add(user_name)
        room.disliked_by.discard(user_name)

        data = {"dislikes": len(room.disliked_by), "likes": len(room.liked_by)}
        await self.connections.notify_all(room_code, user_name, make_event(EventType.LIKES_CHANGED, data))
        return Result.ok(data)

    async def dislike_answer(self, room_code, token):
        user_name = self.token_service.get_user(token)
        if user_name is None:
            return Result.error("Invalid token")

        room = self.room_service.get_room(room_code)
        if room.is_error:
            return room

        room = room.value
        if user_name not in room.users:
            return Result.error('Invalid room')

        if user_name in room.disliked_by:
            return Result.error('Already disliked')

        room.liked_by.discard(user_name)
        room.disliked_by.add(user_name)

        data = {"dislikes": len(room.disliked_by), "likes": len(room.liked_by)}
        await self.connections.notify_all(room_code, user_name, make_event(EventType.LIKES_CHANGED, data))
        return Result.ok(data)
