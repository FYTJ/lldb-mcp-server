class LLDBError(Exception):
    def __init__(self, code, message, data=None):
        super().__init__(message)
        self.code = int(code)
        self.message = str(message)
        self.data = data or {}

    def to_error(self) -> dict:
        return {"code": self.code, "message": self.message, "data": self.data}
