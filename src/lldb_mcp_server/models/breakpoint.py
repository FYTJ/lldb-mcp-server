from typing import List, Optional

from pydantic import BaseModel


class BreakpointLocation(BaseModel):
    address: str
    file: Optional[str] = None
    line: Optional[int] = None
    resolved: Optional[bool] = None


class BreakpointInfo(BaseModel):
    id: int
    enabled: bool
    hitCount: int
    ignoreCount: int
    condition: Optional[str] = None
    locations: List[BreakpointLocation]
