class MasterVerifier:
    def __init__(self):
        self.masters = {}

    def set_master(self, room_code: str, master_token: str):
        self.masters[room_code] = master_token

    def is_master(self, room_code: str, master_token: str):
        return room_code in self.masters and self.masters[room_code] == master_token
