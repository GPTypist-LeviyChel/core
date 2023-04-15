class Connections:
    def __init__(self):
        self._connections = []

    def add_ws_connection(self, ws):
        self._connections.append(ws)

    def remove_ws_connection(self, ws):
        self._connections.remove(ws)

    def notify_all(self, sender: str, payload: dict):
        for ws in self._connections:
            payload["sender"] = sender
            ws.send_json(payload)
