from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models._helpers import new_uuid, utcnow


class ParseError(Base):
    """A line the parser could not confidently interpret. Never silently
    discarded -- always recorded with the raw text and a human-readable
    reason so an analyst can review it (PROJECT_PLAN.md section 7)."""

    __tablename__ = "parse_errors"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    evidence_file_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("evidence_files.id", ondelete="CASCADE"), nullable=False, index=True
    )
    case_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    raw_line: Mapped[str] = mapped_column(Text, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    parser_name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )


class ParsingGap(Base):
    """A detected suspicious gap (large timestamp jump, truncated file,
    etc.) within an evidence file. Recorded, not silently ignored."""

    __tablename__ = "parsing_gaps"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    evidence_file_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("evidence_files.id", ondelete="CASCADE"), nullable=False, index=True
    )
    gap_start_line: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gap_end_line: Mapped[int | None] = mapped_column(Integer, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
