import dataclasses
import secrets

from src.entities.scores import Scores


@dataclasses.dataclass
class User:
    name: str
    profile_pic: int
    is_master: bool

    def __init__(self, name: str, profile_pic: int, is_master: bool = False):
        self.name = name
        self.profile_pic = profile_pic
        self.is_master = is_master
        # self.scores = Scores()
