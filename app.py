import json
import sys

from fastapi import FastAPI, Depends
from starlette.responses import Response
from starlette.websockets import WebSocket

from src.common.result import Result
from src.entities.room import Room
from src.schema import *
from src.services.answer import AnswerService
from src.services.question import QuestionService

# from src.containers import Container
from src.services.room import RoomService

from dependency_injector.containers import DeclarativeContainer
from dependency_injector.providers import Configuration, Factory, Singleton
from dependency_injector.wiring import inject, Provide

from src.services.room import RoomService
from src.services.token import TokenService
from src.session.conenctions import Connections

from dataclass_wizard import asdict


class Container(DeclarativeContainer):
    # config = Configuration()
    connections = Singleton(Connections)
    token_service = Singleton(TokenService)
    room_service = Singleton(RoomService, token_service=token_service)
    question_service = Singleton(QuestionService, room_service=room_service)
    answer_service = Singleton(AnswerService, room_service=room_service, question_server=question_service,
                               connections=connections)


app = FastAPI()


@app.post("/rooms/create", response_model=RoomUserToken)
@inject
async def create_room(master_name: str,
                      room_service: RoomService = Depends(Provide[Container.room_service])):
    result = room_service.create_room(master_name)
    return result.response


@app.post("/rooms/join", response_model=RoomUserToken)
@inject
async def join_room(input: JoinRoom,
                    room_service: RoomService = Depends(Provide[Container.room_service])):
    result = room_service.join_room(input.room_code, input.user_name, input.profile_pic)
    return result.response


@app.post("/rooms/leave")
@inject
async def leave_room(input: LeaveRoom,
                     room_service: RoomService = Depends(Provide[Container.room_service])):
    return room_service.leave_room(input.room_code, input.user_name).response


@app.post("/rooms/start")
@inject
async def start_room(input: StartRoom,
                     room_service: RoomService = Depends(Provide[Container.room_service])):
    return room_service.start_room(input.room_code, input.master_token).only_code


@app.post("/question/answer")
@inject
async def submit_answer(input: SubmitAnswer,
                        token_service: TokenService = Depends(Provide[Container.token_service]),
                        answer_service: AnswerService = Depends(Provide[Container.answer_service])):
    user = token_service.get_user(input.token)
    if user is None:
        return Result.error('Invalid token')
    return answer_service.submit_answer(input.room_code, input.token, input.answer).response


@app.websocket('/ws')
async def websocket_endpoint(websocket: WebSocket, room_code: str,
                             token_service: TokenService = Depends(Provide[Container.token_service]),
                             connections: Connections = Depends(Provide[Container.connections])):
    await websocket.accept()
    connections.add_ws_connection(websocket, room_code)


container = Container()
container.wire(modules=[sys.modules[__name__]])

if __name__ == "__main__":
    import uvicorn

    # start with watch
    uvicorn.run(app, host="0.0.0.0", port=8000)
