from pydantic import BaseModel


class SessionInfo(BaseModel):
    sessionId: str
