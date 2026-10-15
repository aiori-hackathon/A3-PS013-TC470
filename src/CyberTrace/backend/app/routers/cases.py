"""Case CRUD with per-user authorization.

Authorization model (kept deliberately simple for this phase):
- A case created by a user is private to that user unless it is a
  synthetic scenario case (`is_synthetic=True`), which is shared/read-only
  demo data visible to every authenticated user.
- Only the creator (or a user with role 'admin') may view, modify, or
  delete a private case. Synthetic cases cannot be deleted through this
  router (they are managed by the scenario loader in a later phase).
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import get_current_user
from app.models.case import Case
from app.models.evidence import EvidenceFile
from app.models.log_record import LogRecord
from app.models.parse_error import ParseError
from app.models.user import User
from app.schemas.case import CaseCreate, CaseDetailResponse, CaseResponse
from app.services.audit import record_audit_event

router = APIRouter(prefix="/api/cases", tags=["cases"])


def _can_access(case: Case, user: User) -> bool:
    """Read access: owner, admin, or anyone for shared synthetic cases.
    Exported for reuse by the evidence router (same authorization rules
    apply to a case's evidence)."""
    if case.is_synthetic:
        return True
    return case.created_by == user.id or user.role == "admin"


def can_modify(case: Case, user: User) -> bool:
    """Write access (upload evidence, delete case, etc.): owner or admin
    only -- synthetic cases are never writable through these endpoints."""
    if case.is_synthetic:
        return False
    return case.created_by == user.id or user.role == "admin"


async def get_authorized_case(case_id: str, db: AsyncSession, user: User) -> Case:
    """Public wrapper so other routers (evidence) can reuse the same
    case-lookup + authorization check without duplicating logic."""
    return await _get_authorized_case(case_id, db, user)


async def _get_authorized_case(case_id: str, db: AsyncSession, user: User) -> Case:
    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    if case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    if not _can_access(case, user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized for this case")
    return case


@router.get("", response_model=list[CaseResponse])
async def list_cases(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
) -> list[Case]:
    """Returns the current user's own cases plus any synthetic (shared demo)
    cases. Never returns another user's private cases."""
    result = await db.execute(
        select(Case).where(
            (Case.created_by == current_user.id) | (Case.is_synthetic.is_(True))
        ).order_by(Case.created_at.desc())
    )
    return list(result.scalars().all())


@router.post("", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
async def create_case(
    payload: CaseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Case:
    case = Case(
        name=payload.name,
        description=payload.description,
        is_synthetic=False,
        created_by=current_user.id,
    )
    db.add(case)
    await db.commit()
    await db.refresh(case)
    return case


@router.get("/{case_id}", response_model=CaseDetailResponse)
async def get_case(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CaseDetailResponse:
    case = await _get_authorized_case(case_id, db, current_user)

    evidence_count = (
        await db.execute(
            select(func.count()).select_from(EvidenceFile).where(EvidenceFile.case_id == case_id)
        )
    ).scalar_one()
    log_record_count = (
        await db.execute(
            select(func.count()).select_from(LogRecord).where(LogRecord.case_id == case_id)
        )
    ).scalar_one()
    parse_error_count = (
        await db.execute(
            select(func.count()).select_from(ParseError).where(ParseError.case_id == case_id)
        )
    ).scalar_one()

    return CaseDetailResponse(
        id=case.id,
        name=case.name,
        description=case.description,
        is_synthetic=case.is_synthetic,
        scenario_key=case.scenario_key,
        created_by=case.created_by,
        created_at=case.created_at,
        evidence_count=evidence_count,
        log_record_count=log_record_count,
        parse_error_count=parse_error_count,
    )


@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_case(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    case = await _get_authorized_case(case_id, db, current_user)
    if not can_modify(case, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this case"
        )
    await record_audit_event(
        db,
        user_id=current_user.id,
        action="case_delete",
        target_type="case",
        target_id=case.id,
        detail={"name": case.name},
    )
    await db.delete(case)
    await db.commit()
