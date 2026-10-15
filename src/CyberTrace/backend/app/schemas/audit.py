from datetime import datetime

from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    id: str
    user_id: str | None
    action: str
    target_type: str | None
    target_id: str | None
    detail: dict | None
    ip_address: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
