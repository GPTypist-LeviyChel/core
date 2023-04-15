import secrets


class TokenService:
    def __init__(self):
        self._tokens = {}

    def create(self, user: str) -> str:
        token = secrets.token_hex(16)
        self._tokens[token] = user
        return token

    def get_user(self, token) -> str | None:
        return self._tokens.get(token, None)

    def delete(self, token):
        self._tokens.pop(token, None)
