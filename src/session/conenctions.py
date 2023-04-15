from pydantic.utils import defaultdict


class Connections:
    def __init__(self):
        self._connections = defaultdict(list)

    def add_ws_connection(self, ws, room_code: str):
        self._connections[room_code].append(ws)

    def remove_ws_connection(self, ws, room_code: str):
        self._connections[room_code].remove(ws)

    async def notify_all(self, room_code: str, sender: str | None, payload: dict):
        print('notify_all', room_code, sender, payload)

        for ws in self._connections[room_code]:
            payload["sender"] = sender
            try:
                await ws.send_json(payload)
            except Exception as e:
                pass