"""Evidence upload, listing, download, and integrity verification.

Security notes (PROJECT_PLAN.md section 11):
- Uploads are validated by extension allow-list and size limit before any
  bytes are written to disk.
- The original file is written once, unmodified, to a path outside any
  publicly served directory (`EVIDENCE_STORAGE_DIR`, served only through
  this authenticated download endpoint -- never mounted as static files).
- SHA-256 is computed from the exact bytes written to disk at upload time.
- Verification re-reads the stored file and recomputes the hash live --
  it never trusts a cached "verified" flag.
"""
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import get_db
from app.deps import get_current_user
from app.models.evidence import EvidenceFile
from app.models.user import User
from app.routers.cases import can_modify, get_authorized_case
from app.schemas.evidence import EvidenceFileResponse, EvidenceUploadResponse, EvidenceVerifyResponse
from app.security import sha256_of_file
from app.services.audit import record_audit_event
from app.services.format_detection import detect_format
from app.services.ingestion import ingest_evidence_file

router = APIRouter(tags=["evidence"])
settings = get_settings()

ALLOWED_EXTENSIONS = {".log", ".txt", ".json"}


def _storage_root() -> Path:
    root = Path(settings.evidence_storage_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


async def _get_authorized_evidence(
    evidence_id: str, db: AsyncSession, user: User
) -> EvidenceFile:
    result = await db.execute(select(EvidenceFile).where(EvidenceFile.id == evidence_id))
    evidence = result.scalar_one_or_none()
    if evidence is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence file not found")
    # Authorization is derived from the parent case.
    await get_authorized_case(evidence.case_id, db, user)
    return evidence


@router.post(
    "/api/cases/{case_id}/evidence",
    response_model=EvidenceUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_evidence(
    case_id: str,
    file: UploadFile,
    timezone_assumption: str = "UTC",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EvidenceUploadResponse:
    case = await get_authorized_case(case_id, db, current_user)
    if not can_modify(case, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to upload evidence to this case",
        )

    original_filename = file.filename or "unnamed"
    extension = Path(original_filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{extension}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    # Stream to a temp path on disk, enforcing the size limit as we go, so
    # a very large/forged upload cannot exhaust memory before validation.
    storage_root = _storage_root()
    case_dir = storage_root / case_id
    case_dir.mkdir(parents=True, exist_ok=True)
    temp_path = case_dir / f".tmp-{uuid.uuid4().hex}"

    total_bytes = 0
    chunk_size = 1024 * 1024
    try:
        with open(temp_path, "wb") as out:
            while chunk := await file.read(chunk_size):
                total_bytes += len(chunk)
                if total_bytes > settings.max_upload_size_bytes:
                    out.close()
                    os.remove(temp_path)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File exceeds the maximum allowed size of "
                        f"{settings.max_upload_size_bytes} bytes",
                    )
                out.write(chunk)
    finally:
        await file.close()

    if total_bytes == 0:
        os.remove(temp_path)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty")

    # Hash the exact bytes written to disk -- not the in-memory buffer --
    # so the recorded hash reflects what is actually stored and can later
    # be independently re-verified against the stored file.
    sha256_hash = sha256_of_file(temp_path)

    final_path = case_dir / f"{sha256_hash}{extension}"
    os.replace(temp_path, final_path)

    with open(final_path, "r", encoding="utf-8", errors="replace") as f:
        sample_text = f.read(65536)
    detected = detect_format(sample_text)

    evidence = EvidenceFile(
        case_id=case_id,
        original_filename=original_filename,
        detected_format=detected,
        declared_format=None,
        sha256_hash=sha256_hash,
        byte_size=total_bytes,
        storage_path=str(final_path),
        uploaded_by=current_user.id,
        source_timezone_assumption=timezone_assumption,
    )
    db.add(evidence)
    await db.commit()
    await db.refresh(evidence)

    # Run the format-appropriate parser (if any) over the file we just
    # stored -- using `sample_text`-independent full content so every line
    # is covered, not just the detection sample. The original file on disk
    # is never touched by this step; only new log_records/parse_errors/
    # parsing_gaps rows are written.
    with open(final_path, "r", encoding="utf-8", errors="replace") as f:
        full_text = f.read()
    ingestion_result = await ingest_evidence_file(
        db,
        evidence_file_id=evidence.id,
        case_id=case_id,
        detected_format=detected,
        content=full_text,
        timezone_assumption=timezone_assumption,
    )
    await record_audit_event(
        db,
        user_id=current_user.id,
        action="evidence_upload",
        target_type="evidence_file",
        target_id=evidence.id,
        detail={"case_id": case_id, "original_filename": original_filename},
    )
    await db.commit()

    return EvidenceUploadResponse(
        evidence=EvidenceFileResponse.model_validate(evidence),
        records_parsed=ingestion_result.records_parsed,
        records_failed=ingestion_result.records_failed,
        gaps_detected=ingestion_result.gaps_detected,
        automated_seconds=ingestion_result.automated_seconds,
        manual_estimate_seconds=ingestion_result.manual_estimate_seconds,
    )


@router.get("/api/cases/{case_id}/evidence", response_model=list[EvidenceFileResponse])
async def list_evidence(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[EvidenceFile]:
    await get_authorized_case(case_id, db, current_user)
    result = await db.execute(
        select(EvidenceFile)
        .where(EvidenceFile.case_id == case_id)
        .order_by(EvidenceFile.uploaded_at.desc())
    )
    return list(result.scalars().all())


@router.get("/api/evidence/{evidence_id}/download")
async def download_evidence(
    evidence_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FileResponse:
    evidence = await _get_authorized_evidence(evidence_id, db, current_user)
    if not os.path.exists(evidence.storage_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Stored evidence file is missing on disk"
        )
    return FileResponse(
        path=evidence.storage_path,
        filename=evidence.original_filename,
        media_type="application/octet-stream",
    )


@router.get("/api/evidence/{evidence_id}/verify", response_model=EvidenceVerifyResponse)
async def verify_evidence(
    evidence_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EvidenceVerifyResponse:
    """Recomputes the SHA-256 of the file currently stored on disk and
    compares it against the hash recorded at upload time. This is a live
    check -- it reads the file fresh every call, it does not cache a
    pass/fail result."""
    evidence = await _get_authorized_evidence(evidence_id, db, current_user)

    if not os.path.exists(evidence.storage_path):
        return EvidenceVerifyResponse(
            evidence_id=evidence.id,
            verified=False,
            recorded_sha256=evidence.sha256_hash,
            recomputed_sha256=None,
            error="Stored evidence file is missing on disk",
            checked_at=datetime.now(timezone.utc),
        )

    try:
        recomputed = sha256_of_file(evidence.storage_path)
    except OSError as exc:
        return EvidenceVerifyResponse(
            evidence_id=evidence.id,
            verified=False,
            recorded_sha256=evidence.sha256_hash,
            recomputed_sha256=None,
            error=f"Could not read stored file: {exc}",
            checked_at=datetime.now(timezone.utc),
        )

    return EvidenceVerifyResponse(
        evidence_id=evidence.id,
        verified=recomputed == evidence.sha256_hash,
        recorded_sha256=evidence.sha256_hash,
        recomputed_sha256=recomputed,
        error=None,
        checked_at=datetime.now(timezone.utc),
    )
