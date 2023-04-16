import asyncio
import json
import sys
from ssl import SSLContext, PROTOCOL_TLSv1_2

from fastapi import FastAPI, Depends
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.websockets import WebSocket

from src.common.result import Result
from src.entities.room import Room
from src.schema import *
from src.services.master import MasterVerifier
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
    master_verify = Singleton(MasterVerifier)
    room_service = Singleton(RoomService, token_service=token_service, master_verify=master_verify,
                             connections=connections)
    question_service = Singleton(QuestionService, room_service=room_service, token_service=token_service,
                                 master_verify=master_verify, connections=connections)


app = FastAPI()

origins = ["https://scrum.mom"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/rooms/create", response_model=RoomUserToken)
@inject
async def create_room(input: CreateRoom,
                      room_service: RoomService = Depends(Provide[Container.room_service])):
    result = await room_service.create_room(input.con_token, input.master_name, input.questions_per_user or 1)
    return result.response


@app.post("/rooms/join", response_model=RoomUserToken)
@inject
async def join_room(input: JoinRoom,
                    room_service: RoomService = Depends(Provide[Container.room_service])):
    result = await room_service.join_room(input.con_token, input.room_code, input.user_name)
    return result.response


@app.post("/rooms/leave")
@inject
async def leave_room(input: LeaveRoom,
                     room_service: RoomService = Depends(Provide[Container.room_service])):
    return (await room_service.leave_room(input.con_token)).response


@app.post("/rooms/start")
@inject
async def start_room(input: StartRoom,
                     question_service: QuestionService = Depends(Provide[Container.question_service])):
    return (await question_service.start_game(input.room_code, input.master_token)).response


@app.post("/question/answer")
@inject
async def submit_answer(input: SubmitAnswer,
                        question_service: QuestionService = Depends(Provide[Container.question_service])):
    return (await question_service.submit_answer(input.room_code, input.token, input.answer)).response


@app.post("/question/next")
@inject
async def next_question(input: NextQuestion,
                        question_service: QuestionService = Depends(Provide[Container.question_service])):
    return (await question_service.next_question(input.room_code, input.token)).response


@app.post("/question/like")
@inject
async def like_answer(input: LikeAnswer,
                      question_service: QuestionService = Depends(Provide[Container.question_service])):
    return (await question_service.like_answer(input.room_code, input.token)).response


@app.post("/question/dislike")
@inject
async def like_answer(input: LikeAnswer,
                      question_service: QuestionService = Depends(Provide[Container.question_service])):
    return (await question_service.dislike_answer(input.room_code, input.token)).response


# join room by code
@app.get('/{room_code: [A-Z0-9]{6}')
async def join_room_by_code(room_code: str):
    return JSONResponse({'room_code': room_code})


@app.websocket('/ws')
@inject
async def websocket_endpoint(websocket: WebSocket,
                             room_service: RoomService = Depends(Provide[Container.room_service]),
                             connections: Connections = Depends(Provide[Container.connections])):
    await websocket.accept()
    token = websocket.query_params.get('token')
    token = token.strip()
    if not token:
        await websocket.close()
        return

    connections.add_ws_connection(websocket, token)

    while True:
        try:
            data = await websocket.receive_text()
        except Exception as e:
            await room_service.leave_room(token)
            connections.remove_ws_connection(websocket, token)
            print('exception', e)
            return

        if data == 'pong':
            await asyncio.sleep(1)
            await websocket.send_json({'type': 0})
        else:
            await room_service.leave_room(token)
            connections.remove_ws_connection(websocket, token)
            break


container = Container()
container.wire(modules=[sys.modules[__name__]])



if __name__ == "__main__":
    import uvicorn

    # start with watch
    uvicorn.run(app, host="0.0.0.0", port=8001, ssl_certfile='fullchain.pem', ssl_keyfile='key.pem')
