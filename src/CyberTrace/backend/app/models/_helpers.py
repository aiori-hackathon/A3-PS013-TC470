"""Small shared helpers used across SQLAlchemy models."""
import uuid
from datetime import datetime, timezone


def new_uuid() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    """Current time as a timezone-aware UTC datetime.

    All timestamps in CyberTrace are stored in UTC -- see
    docs/TIMEZONE_POLICY.md for the full normalization/clock-skew policy.
    """
    return datetime.now(timezone.utc)
