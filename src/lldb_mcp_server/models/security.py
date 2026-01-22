from typing import List, Optional

from pydantic import BaseModel


class CrashIndicator(BaseModel):
    type: str
    description: str
    severity: str


class CrashAnalysis(BaseModel):
    rating: str
    confidence: float
    crashType: str
    accessType: str
    faultAddress: Optional[str] = None
    instruction: Optional[dict] = None
    registers: Optional[dict] = None
    indicators: List[CrashIndicator]
    recommendation: str


class SuspiciousFunction(BaseModel):
    name: str
    address: Optional[str] = None
    frameIndex: Optional[int] = None
    category: str
    risk: str
    description: str


class SuspiciousSummary(BaseModel):
    totalFunctions: int
    highRisk: int
    mediumRisk: int
    lowRisk: int
