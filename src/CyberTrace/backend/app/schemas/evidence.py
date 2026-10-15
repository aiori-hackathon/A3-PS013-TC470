from datetime import datetime

from pydantic import BaseModel


class EvidenceFileResponse(BaseModel):
    id: str
    case_id: str
    original_filename: str
    detected_format: str
    declared_format: str | None
    sha256_hash: str
    byte_size: int
    uploaded_by: str | None
    uploaded_at: datetime
    source_timezone_assumption: str
    notes: str | None

    model_config = {"from_attributes": True}


class EvidenceUploadResponse(BaseModel):
    evidence: EvidenceFileResponse
    records_parsed: int
    records_failed: int
    gaps_detected: int
    # Triage-time comparison (PROJECT_PLAN.md section 1): automated_seconds
    # is a real wall-clock measurement of the parse+ingest stage;
    # manual_estimate_seconds is an explicit, labeled assumption (lines x a
    # fixed seconds-per-line constant), never presented as measured fact.
    automated_seconds: float
    manual_estimate_seconds: float


class EvidenceVerifyResponse(BaseModel):
    evidence_id: str
    verified: bool
    recorded_sha256: str
    recomputed_sha256: str | None
    error: str | None
    checked_at: datetime
