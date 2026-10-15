from datetime import datetime

from pydantic import BaseModel


class ReportResponse(BaseModel):
    id: str
    case_id: str
    format: str
    generated_by: str | None
    generated_at: datetime

    model_config = {"from_attributes": True}
