"""Report export endpoints: JSON / CSV (zipped) / PDF, per
PROJECT_PLAN.md section 10. Generation reads the same real DB rows used
by the Timeline/Evidence/Parse-Errors pages -- no separate invented
statistics -- and the generated file is written once to
`REPORTS_STORAGE_DIR` and recorded in the `reports` table for later
download, mirroring the evidence-preservation pattern used for uploads.
"""
import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import get_db
from app.deps import get_current_user
from app.models.evidence import EvidenceFile
from app.models.log_record import LogRecord
from app.models.parse_error import ParseError, ParsingGap
from app.models.report import Report
from app.models.user import User
from app.routers.cases import get_authorized_case
from app.schemas.report import ReportResponse
from app.services.audit import record_audit_event
from app.services.report_export import build_csv_export_zip, build_json_export, build_pdf_report

router = APIRouter(tags=["reports"])
settings = get_settings()

ALLOWED_FORMATS = {"json", "csv", "pdf"}
_FORMAT_EXTENSION = {"json": ".json", "csv": ".zip", "pdf": ".pdf"}
_FORMAT_MEDIA_TYPE = {
    "json": "application/json",
    "csv": "application/zip",
    "pdf": "application/pdf",
}


def _reports_root() -> Path:
    root = Path(settings.reports_storage_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


async def _load_case_data(db: AsyncSession, case_id: str):
    evidence_files = list(
        (await db.execute(select(EvidenceFile).where(EvidenceFile.case_id == case_id)))
        .scalars()
        .all()
    )
    log_records = list(
        (
            await db.execute(
                select(LogRecord)
                .where(LogRecord.case_id == case_id)
                .order_by(LogRecord.event_time_utc.asc())
            )
        )
        .scalars()
        .all()
    )
    parse_errors = list(
        (await db.execute(select(ParseError).where(ParseError.case_id == case_id)))
        .scalars()
        .all()
    )
    evidence_ids = [e.id for e in evidence_files]
    parsing_gaps: list[ParsingGap] = []
    if evidence_ids:
        parsing_gaps = list(
            (
                await db.execute(
                    select(ParsingGap).where(ParsingGap.evidence_file_id.in_(evidence_ids))
                )
            )
            .scalars()
            .all()
        )
    return evidence_files, log_records, parse_errors, parsing_gaps


@router.post(
    "/api/cases/{case_id}/reports",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
)
async def generate_report(
    case_id: str,
    format: str = Query(..., pattern="^(json|csv|pdf)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Report:
    case = await get_authorized_case(case_id, db, current_user)
    evidence_files, log_records, parse_errors, parsing_gaps = await _load_case_data(db, case_id)

    if format == "json":
        payload = build_json_export(case, evidence_files, log_records, parse_errors, parsing_gaps)
        content = json.dumps(payload, indent=2).encode("utf-8")
    elif format == "csv":
        content = build_csv_export_zip(log_records, parse_errors)
    else:
        content = build_pdf_report(case, evidence_files, log_records, parse_errors, parsing_gaps)

    report_id_dir = _reports_root() / case_id
    report_id_dir.mkdir(parents=True, exist_ok=True)
    report = Report(case_id=case_id, format=format, generated_by=current_user.id, storage_path="")
    file_path = report_id_dir / f"{report.id}{_FORMAT_EXTENSION[format]}"
    file_path.write_bytes(content)
    report.storage_path = str(file_path)

    db.add(report)
    await record_audit_event(
        db,
        user_id=current_user.id,
        action="report_export",
        target_type="report",
        target_id=report.id,
        detail={"case_id": case_id, "format": format},
    )
    await db.commit()
    await db.refresh(report)
    return report


@router.get("/api/cases/{case_id}/reports", response_model=list[ReportResponse])
async def list_reports(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Report]:
    await get_authorized_case(case_id, db, current_user)
    result = await db.execute(
        select(Report).where(Report.case_id == case_id).order_by(Report.generated_at.desc())
    )
    return list(result.scalars().all())


@router.get("/api/reports/{report_id}/download")
async def download_report(
    report_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FileResponse:
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalar_one_or_none()
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    await get_authorized_case(report.case_id, db, current_user)

    if not Path(report.storage_path).exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Stored report file is missing on disk"
        )

    filename = f"cybertrace_report_{report.case_id}{_FORMAT_EXTENSION[report.format]}"
    return FileResponse(
        path=report.storage_path,
        filename=filename,
        media_type=_FORMAT_MEDIA_TYPE[report.format],
    )
