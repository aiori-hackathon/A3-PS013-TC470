from datetime import datetime

from pydantic import BaseModel


class TimelineRecordResponse(BaseModel):
    id: str
    case_id: str
    evidence_file_id: str
    line_number: int
    raw_line: str
    event_time_utc: datetime
    original_timezone: str
    source_ip: str | None
    user_or_actor: str | None
    event_type: str
    message: str
    severity: str
    extra: dict | None
    # Denormalized from the parent evidence_files row so the timeline table
    # can show "source evidence" (filename + hash) without a second
    # round-trip per row (PROJECT_PLAN.md section 1A.A, item 7).
    evidence_filename: str
    evidence_sha256: str
    # True if a parsing_gaps row for this evidence file brackets this
    # record's line_number -- drives the "Near parse gap" badge.
    near_parse_gap: bool

    model_config = {"from_attributes": True}


class TimelineResponse(BaseModel):
    total: int
    limit: int
    offset: int
    records: list[TimelineRecordResponse]
