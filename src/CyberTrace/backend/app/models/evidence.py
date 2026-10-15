from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models._helpers import new_uuid, utcnow


class EvidenceFile(Base):
    """One row per uploaded raw file. The underlying file on disk is never
    modified after upload -- see docs/TIMEZONE_POLICY.md and
    PROJECT_PLAN.md section 8 (Evidence Preservation)."""

    __tablename__ = "evidence_files"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    case_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    detected_format: Mapped[str] = mapped_column(String(50), nullable=False)
    declared_format: Mapped[str | None] = mapped_column(String(50), nullable=True)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    byte_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    uploaded_by: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=True
    )
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    # Timezone assumption applied for formats without an embedded UTC offset
    # (e.g. classic syslog). See docs/TIMEZONE_POLICY.md.
    source_timezone_assumption: Mapped[str] = mapped_column(String(100), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
