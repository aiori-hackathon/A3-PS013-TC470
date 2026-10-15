from datetime import datetime

from pydantic import BaseModel, Field


class CaseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)


class CaseResponse(BaseModel):
    id: str
    name: str
    description: str | None
    is_synthetic: bool
    scenario_key: str | None
    created_by: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class CaseDetailResponse(CaseResponse):
    evidence_count: int
    log_record_count: int
    parse_error_count: int
