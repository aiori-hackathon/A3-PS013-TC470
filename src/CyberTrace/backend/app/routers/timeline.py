"""Case timeline: searchable, filterable, paginated view over normalized
`log_records`, per PROJECT_PLAN.md section 1A.A.

Every control on the Timeline page (search, date range, event type,
severity, source, sort, pagination) is backed by real query parameters
here -- never client-side mock filtering.
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import get_current_user
from app.models.evidence import EvidenceFile
from app.models.log_record import LogRecord
from app.models.parse_error import ParsingGap
from app.models.user import User
from app.routers.cases import get_authorized_case
from app.schemas.timeline import TimelineRecordResponse, TimelineResponse

router = APIRouter(prefix="/api/cases", tags=["timeline"])

ALLOWED_SORT_FIELDS = {"event_time_utc"}


@router.get("/{case_id}/timeline", response_model=TimelineResponse)
async def get_timeline(
    case_id: str,
    q: str | None = Query(default=None, description="Free-text search over message/raw_line"),
    start_time: datetime | None = Query(default=None),
    end_time: datetime | None = Query(default=None),
    event_type: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    source: str | None = Query(
        default=None, description="Matches source_ip or user_or_actor"
    ),
    sort: str = Query(default="event_time_utc"),
    order: str = Query(default="asc", pattern="^(asc|desc)$"),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TimelineResponse:
    await get_authorized_case(case_id, db, current_user)

    if sort not in ALLOWED_SORT_FIELDS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported sort field '{sort}'. Allowed: {', '.join(sorted(ALLOWED_SORT_FIELDS))}",
        )

    base_query = select(LogRecord).where(LogRecord.case_id == case_id)
    count_query = select(func.count()).select_from(LogRecord).where(LogRecord.case_id == case_id)

    if q:
        like = f"%{q}%"
        text_filter = or_(LogRecord.message.ilike(like), LogRecord.raw_line.ilike(like))
        base_query = base_query.where(text_filter)
        count_query = count_query.where(text_filter)
    if start_time:
        base_query = base_query.where(LogRecord.event_time_utc >= start_time)
        count_query = count_query.where(LogRecord.event_time_utc >= start_time)
    if end_time:
        base_query = base_query.where(LogRecord.event_time_utc <= end_time)
        count_query = count_query.where(LogRecord.event_time_utc <= end_time)
    if event_type:
        base_query = base_query.where(LogRecord.event_type == event_type)
        count_query = count_query.where(LogRecord.event_type == event_type)
    if severity:
        base_query = base_query.where(LogRecord.severity == severity)
        count_query = count_query.where(LogRecord.severity == severity)
    if source:
        like = f"%{source}%"
        source_filter = or_(
            LogRecord.source_ip.ilike(like), LogRecord.user_or_actor.ilike(like)
        )
        base_query = base_query.where(source_filter)
        count_query = count_query.where(source_filter)

    total = (await db.execute(count_query)).scalar_one()

    sort_column = getattr(LogRecord, sort)
    sort_column = sort_column.desc() if order == "desc" else sort_column.asc()
    base_query = base_query.order_by(sort_column).limit(limit).offset(offset)

    records = list((await db.execute(base_query)).scalars().all())

    if not records:
        return TimelineResponse(total=total, limit=limit, offset=offset, records=[])

    evidence_file_ids = {r.evidence_file_id for r in records}
    evidence_result = await db.execute(
        select(EvidenceFile).where(EvidenceFile.id.in_(evidence_file_ids))
    )
    evidence_by_id = {e.id: e for e in evidence_result.scalars().all()}

    gaps_result = await db.execute(
        select(ParsingGap).where(ParsingGap.evidence_file_id.in_(evidence_file_ids))
    )
    gaps_by_evidence: dict[str, list[ParsingGap]] = {}
    for gap in gaps_result.scalars().all():
        gaps_by_evidence.setdefault(gap.evidence_file_id, []).append(gap)

    def _is_near_gap(record: LogRecord) -> bool:
        for gap in gaps_by_evidence.get(record.evidence_file_id, []):
            start = gap.gap_start_line
            end = gap.gap_end_line
            if start is not None and end is not None and start <= record.line_number <= end:
                return True
        return False

    response_records = []
    for record in records:
        evidence = evidence_by_id.get(record.evidence_file_id)
        response_records.append(
            TimelineRecordResponse(
                id=record.id,
                case_id=record.case_id,
                evidence_file_id=record.evidence_file_id,
                line_number=record.line_number,
                raw_line=record.raw_line,
                event_time_utc=record.event_time_utc,
                original_timezone=record.original_timezone,
                source_ip=record.source_ip,
                user_or_actor=record.user_or_actor,
                event_type=record.event_type,
                message=record.message,
                severity=record.severity,
                extra=record.extra,
                evidence_filename=evidence.original_filename if evidence else "unknown",
                evidence_sha256=evidence.sha256_hash if evidence else "",
                near_parse_gap=_is_near_gap(record),
            )
        )

    return TimelineResponse(total=total, limit=limit, offset=offset, records=response_records)
