from pydantic import BaseModel

from app.schemas.case import CaseResponse


class ScenarioInfo(BaseModel):
    key: str
    name: str
    description: str


class ScenarioLoadResponse(BaseModel):
    case: CaseResponse
    records_parsed: int
    records_failed: int
    gaps_detected: int
