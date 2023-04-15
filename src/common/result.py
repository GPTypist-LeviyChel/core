from starlette.responses import Response


class Result:
    def __init__(self, value, err_message: str = None):
        self.value = value
        self.err_message = err_message

    @staticmethod
    def ok(value=None) -> 'Result':
        return Result(value, None)

    @staticmethod
    def error(message: str) -> 'Result':
        return Result(None, message)

    @property
    def is_ok(self) -> bool:
        return self.err_message is None

    @property
    def is_error(self) -> bool:
        return not self.is_ok

    @property
    def response(self):
        if self.is_ok:
            return self.value

        return Response(self.err_message, status_code=400)

    def match(self, ok_fn, err_fn=None):
        if self.is_ok:
            return ok_fn(self.value)

        if err_fn is None:
            return self.response
        return err_fn(self.err_message)
