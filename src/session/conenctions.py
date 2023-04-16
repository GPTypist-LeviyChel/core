from pydantic.utils import defaultdict


class Connections:
    def __init__(self):
        self._connections = defaultdict(list)
        self._all_connections = {}
        self._association = {}

    def add_ws_connection(self, ws, token: str):
        self._all_connections[token] = ws

    def associate(self, token: str, pair: tuple):
        self._association[token] = pair
        self._connections[pair[0]].append(self._all_connections[token])

    def remove_ws_connection(self, ws, token: str):
        assoc = self._association.get(token, None)
        if assoc:
            self._association.pop(token)
            self._connections[assoc[0]].remove(ws)
        self._all_connections.pop(token)

    def get_assoc(self, token: str):
        return self._association.get(token, None)

    async def notify_all(self, room_code: str, sender: str | None, payload: dict):
        print('notify_all', room_code, sender, payload)

        for ws in self._connections[room_code]:
            payload["sender"] = sender
            print('sending to', ws, room_code)
            try:
                await ws.send_json(payload)
            except Exception as e:
                pass
