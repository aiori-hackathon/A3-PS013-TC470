"""Parse Errors & Limitations view: combined `parse_errors` +
`parsing_gaps` for a case, per PROJECT_PLAN.md section 1A.C -- "never
buried or omitted from navigation". Read-only, same per-user case
authorization as every other case-scoped endpoint.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import get_current_user
from app.models.evidence import EvidenceFile
from app.models.parse_error import ParseError, ParsingGap
from app.models.user import User
from app.routers.cases import get_authorized_case
from app.schemas.parse_issues import (
    ParseErrorResponse,
    ParseIssuesResponse,
    ParsingGapResponse,
)

router = APIRouter(prefix="/api/cases", tags=["parse-issues"])


@router.get("/{case_id}/parse-issues", response_model=ParseIssuesResponse)
async def get_parse_issues(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ParseIssuesResponse:
    await get_authorized_case(case_id, db, current_user)

    errors_result = await db.execute(
        select(ParseError)
        .where(ParseError.case_id == case_id)
        .order_by(ParseError.created_at.desc())
    )
    errors = list(errors_result.scalars().all())

    evidence_result = await db.execute(
        select(EvidenceFile).where(EvidenceFile.case_id == case_id)
    )
    evidence_by_id = {e.id: e for e in evidence_result.scalars().all()}

    gaps: list[ParsingGap] = []
    if evidence_by_id:
        gaps_result = await db.execute(
            select(ParsingGap).where(ParsingGap.evidence_file_id.in_(evidence_by_id.keys()))
        )
        gaps = list(gaps_result.scalars().all())

    error_responses = [
        ParseErrorResponse(
            id=e.id,
            evidence_file_id=e.evidence_file_id,
            case_id=e.case_id,
            line_number=e.line_number,
            raw_line=e.raw_line,
            reason=e.reason,
            parser_name=e.parser_name,
            created_at=e.created_at,
            evidence_filename=evidence_by_id[e.evidence_file_id].original_filename
            if e.evidence_file_id in evidence_by_id
            else "unknown",
        )
        for e in errors
    ]
    gap_responses = [
        ParsingGapResponse(
            id=g.id,
            evidence_file_id=g.evidence_file_id,
            gap_start_line=g.gap_start_line,
            gap_end_line=g.gap_end_line,
            description=g.description,
            created_at=g.created_at,
            evidence_filename=evidence_by_id[g.evidence_file_id].original_filename
            if g.evidence_file_id in evidence_by_id
            else "unknown",
        )
        for g in gaps
    ]

    return ParseIssuesResponse(parse_errors=error_responses, parsing_gaps=gap_responses)
