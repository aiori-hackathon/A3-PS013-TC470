from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models._helpers import new_uuid


class LogRecord(Base):
    """A successfully parsed and normalized event. `raw_line` always keeps
    the original, unmodified source text so every normalized fact is
    traceable back to the evidence it came from."""

    __tablename__ = "log_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    evidence_file_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("evidence_files.id", ondelete="CASCADE"), nullable=False, index=True
    )
    case_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    raw_line: Mapped[str] = mapped_column(Text, nullable=False)
    event_time_utc: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    original_timezone: Mapped[str] = mapped_column(String(100), nullable=False)
    clock_skew_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_ip: Mapped[str | None] = mapped_column(String(100), nullable=True)
    user_or_actor: Mapped[str | None] = mapped_column(String(255), nullable=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="info")
    extra: Mapped[dict | None] = mapped_column(JSON, nullable=True)
