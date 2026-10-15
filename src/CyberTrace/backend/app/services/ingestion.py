"""Ingestion service: runs the format-appropriate parser over a freshly
uploaded evidence file's content and persists the results.

Per PROJECT_PLAN.md section 7:
- Each parsed line becomes exactly one `LogRecord` or one `ParseError` --
  nothing is silently dropped.
- A gap-detection heuristic flags suspiciously large jumps between
  consecutive successfully-parsed timestamps as a `ParsingGap` row.
- The caller gets back honest `records_parsed` / `records_failed` /
  `gaps_detected` counts derived from what was actually written to the DB.

Triage-time comparison: `automated_seconds` is a real wall-clock
measurement of this function's own parse+DB-stage work (not the full HTTP
request/hashing time). `manual_estimate_seconds` is explicitly an
assumption-based estimate (`SECONDS_PER_LINE_MANUAL_ESTIMATE` applied to
the real line count), surfaced to the UI labeled as an estimate -- never
presented as a measured fact, matching the same
"assumption vs. measured value, always labeled" pattern used for
timezones (docs/TIMEZONE_POLICY.md).
"""
import time
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.log_record import LogRecord
from app.models.parse_error import ParseError, ParsingGap
from app.parsers import PARSERS
from app.parsers.base import ParseErrorRecord, ParsedRecord

# If consecutive successfully-parsed records jump by more than this, it is
# recorded as a parsing_gaps row (PROJECT_PLAN.md section 7: "large jump in
# line timestamps"). Chosen as a conservative default for demo-scale log
# files; not user-configurable yet.
GAP_THRESHOLD_SECONDS = 3600

# Assumption, not a measurement: a conservative estimate of how long a
# human analyst takes to read, interpret, and record one raw log line
# during manual triage. Deliberately labeled as an estimate everywhere
# it's surfaced -- see docs/TIMEZONE_POLICY.md for the project's general
# "assumptions must be visible, not silently presented as fact" principle.
SECONDS_PER_LINE_MANUAL_ESTIMATE = 15


@dataclass
class IngestionResult:
    records_parsed: int
    records_failed: int
    gaps_detected: int
    automated_seconds: float
    manual_estimate_seconds: float


async def ingest_evidence_file(
    db: AsyncSession,
    *,
    evidence_file_id: str,
    case_id: str,
    detected_format: str,
    content: str,
    timezone_assumption: str,
) -> IngestionResult:
    start_time = time.monotonic()

    parser = PARSERS.get(detected_format)
    if parser is None:
        # Unknown/unsupported format: nothing to parse, but this is not an
        # error condition in itself -- the evidence file is still stored
        # and downloadable, it simply has no derived records yet.
        return IngestionResult(
            records_parsed=0,
            records_failed=0,
            gaps_detected=0,
            automated_seconds=time.monotonic() - start_time,
            manual_estimate_seconds=0.0,
        )

    parsed_lines = parser(content, timezone_assumption)

    records_parsed = 0
    records_failed = 0
    last_record: ParsedRecord | None = None
    gaps_detected = 0

    for line in parsed_lines:
        if isinstance(line, ParseErrorRecord):
            db.add(
                ParseError(
                    evidence_file_id=evidence_file_id,
                    case_id=case_id,
                    line_number=line.line_number,
                    raw_line=line.raw_line,
                    reason=line.reason,
                    parser_name=detected_format,
                )
            )
            records_failed += 1
            continue

        if last_record is not None:
            delta = abs(
                (line.event_time_utc - last_record.event_time_utc).total_seconds()
            )
            if delta > GAP_THRESHOLD_SECONDS:
                db.add(
                    ParsingGap(
                        evidence_file_id=evidence_file_id,
                        gap_start_line=last_record.line_number,
                        gap_end_line=line.line_number,
                        description=(
                            f"Timestamp jump of {int(delta)}s between line "
                            f"{last_record.line_number} and {line.line_number}"
                        ),
                    )
                )
                gaps_detected += 1

        db.add(
            LogRecord(
                evidence_file_id=evidence_file_id,
                case_id=case_id,
                line_number=line.line_number,
                raw_line=line.raw_line,
                event_time_utc=line.event_time_utc,
                original_timezone=line.original_timezone,
                source_ip=line.source_ip,
                user_or_actor=line.user_or_actor,
                event_type=line.event_type,
                message=line.message,
                severity=line.severity,
                extra=line.extra,
            )
        )
        records_parsed += 1
        last_record = line

    total_lines = records_parsed + records_failed
    return IngestionResult(
        records_parsed=records_parsed,
        records_failed=records_failed,
        gaps_detected=gaps_detected,
        automated_seconds=time.monotonic() - start_time,
        manual_estimate_seconds=total_lines * SECONDS_PER_LINE_MANUAL_ESTIMATE,
    )
