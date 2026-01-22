from typing import Optional

from pydantic import BaseModel


class ProcessInfo(BaseModel):
    pid: Optional[int] = None
    state: Optional[str] = None


class ThreadInfo(BaseModel):
    id: int
    name: Optional[str] = None
    state: Optional[str] = None
    stopReason: Optional[str] = None
    frameCount: Optional[int] = None


class FrameInfo(BaseModel):
    index: int
    function: str
    file: Optional[str] = None
    line: Optional[int] = None
    address: Optional[str] = None
