import secrets

from src.entities.scores import Scores


class User:
    def __init__(self, _id: int, name: str, profile_pic: int, master_token: str = None):
        self.id = _id
        self.name = name
        self.profile_pic = profile_pic
        if master_token:
            self.token = master_token
            self.is_master = True
        else:
            self.token = secrets.token_hex(16)
            self.is_master = False
        self.scores = Scores()
