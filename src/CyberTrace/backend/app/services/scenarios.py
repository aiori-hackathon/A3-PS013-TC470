"""Synthetic incident scenario loader, per PROJECT_PLAN.md section 9.

Each scenario loads a committed sample log from `backend/sample_logs/`
into a fresh `is_synthetic=True` case, going through the exact same
hash/store/detect/ingest pipeline as a real upload (reusing
`app.security.sha256_of_bytes`, `app.services.format_detection.detect_format`,
and `app.services.ingestion.ingest_evidence_file`) so scenario data is
reproducible and traceable the same way real evidence is -- not a
separate, less-trustworthy code path.
"""
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.case import Case
from app.models.evidence import EvidenceFile
from app.security import sha256_of_bytes
from app.services.format_detection import detect_format
from app.services.ingestion import ingest_evidence_file

settings = get_settings()

SAMPLE_LOGS_DIR = Path(__file__).resolve().parent.parent.parent / "sample_logs"

SCENARIOS = {
    "ssh_bruteforce": {
        "name": "SSH Brute Force (synthetic)",
        "description": (
            "Repeated failed SSH logins from a small set of IPs against auth.log, "
            "culminating in one successful login and a suspicious sudo command. "
            "Includes a few corrupted/truncated lines to exercise parse-error handling."
        ),
        "sample_file": "ssh_bruteforce.log",
        "timezone_assumption": "UTC",
    },
    "sql_injection_probe": {
        "name": "SQL Injection Probe (synthetic)",
        "description": (
            "Apache/Nginx access log showing a scanner probing query parameters "
            "with SQLi payloads, mixed with normal traffic, including malformed lines."
        ),
        "sample_file": "sql_injection_probe.log",
        "timezone_assumption": "UTC",
    },
    "phishing_lateral_movement": {
        "name": "Phishing + Lateral Movement (synthetic)",
        "description": (
            "Windows Event Log JSON export showing a suspicious remote logon, "
            "new-process creation, and privilege escalation shortly after -- "
            "includes a deliberate mid-sequence clock-skew inconsistency."
        ),
        "sample_file": "phishing_lateral_movement.json",
        "timezone_assumption": "UTC",
    },
}


def _storage_root() -> Path:
    root = Path(settings.evidence_storage_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


async def load_scenario(db: AsyncSession, scenario_key: str, created_by: str) -> dict:
    """Loads the named scenario into a brand-new synthetic case. Returns a
    summary dict with the created case id and real ingestion counts."""
    scenario = SCENARIOS[scenario_key]
    sample_path = SAMPLE_LOGS_DIR / scenario["sample_file"]
    content_bytes = sample_path.read_bytes()
    content_text = content_bytes.decode("utf-8", errors="replace")

    case = Case(
        name=scenario["name"],
        description=scenario["description"],
        is_synthetic=True,
        scenario_key=scenario_key,
        created_by=created_by,
    )
    db.add(case)
    await db.flush()  # assigns case.id without committing yet

    sha256_hash = sha256_of_bytes(content_bytes)
    extension = sample_path.suffix
    case_dir = _storage_root() / case.id
    case_dir.mkdir(parents=True, exist_ok=True)
    final_path = case_dir / f"{sha256_hash}{extension}"
    final_path.write_bytes(content_bytes)

    detected = detect_format(content_text[:65536])

    evidence = EvidenceFile(
        case_id=case.id,
        original_filename=scenario["sample_file"],
        detected_format=detected,
        declared_format=None,
        sha256_hash=sha256_hash,
        byte_size=len(content_bytes),
        storage_path=str(final_path),
        uploaded_by=created_by,
        source_timezone_assumption=scenario["timezone_assumption"],
    )
    db.add(evidence)
    await db.flush()

    ingestion_result = await ingest_evidence_file(
        db,
        evidence_file_id=evidence.id,
        case_id=case.id,
        detected_format=detected,
        content=content_text,
        timezone_assumption=scenario["timezone_assumption"],
    )
    await db.commit()
    await db.refresh(case)

    return {
        "case": case,
        "records_parsed": ingestion_result.records_parsed,
        "records_failed": ingestion_result.records_failed,
        "gaps_detected": ingestion_result.gaps_detected,
    }
