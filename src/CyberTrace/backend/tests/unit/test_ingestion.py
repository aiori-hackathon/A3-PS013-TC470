"""Unit tests for the ingestion service: that parsed records/errors are
persisted with correct line numbers, that raw text is preserved verbatim,
and that large timestamp jumps are recorded as parsing_gaps rows."""
import pytest
from sqlalchemy import select

from app.models.log_record import LogRecord
from app.models.parse_error import ParseError, ParsingGap
from app.services.ingestion import ingest_evidence_file


@pytest.mark.asyncio
async def test_ingest_writes_log_records_and_parse_errors(db_session):
    content = (
        "Oct 10 13:55:36 server sshd[1]: Failed password for root from 1.2.3.4 port 1 ssh2\n"
        "not a valid syslog line\n"
    )
    result = await ingest_evidence_file(
        db_session,
        evidence_file_id="ev-1",
        case_id="case-1",
        detected_format="syslog_auth",
        content=content,
        timezone_assumption="UTC",
    )
    await db_session.commit()

    assert result.records_parsed == 1
    assert result.records_failed == 1

    records = (await db_session.execute(select(LogRecord))).scalars().all()
    errors = (await db_session.execute(select(ParseError))).scalars().all()

    assert len(records) == 1
    assert records[0].line_number == 1
    assert records[0].raw_line == (
        "Oct 10 13:55:36 server sshd[1]: Failed password for root from 1.2.3.4 port 1 ssh2"
    )
    assert records[0].evidence_file_id == "ev-1"
    assert records[0].case_id == "case-1"

    assert len(errors) == 1
    assert errors[0].line_number == 2
    assert errors[0].raw_line == "not a valid syslog line"
    assert errors[0].parser_name == "syslog_auth"


@pytest.mark.asyncio
async def test_ingest_detects_large_timestamp_gap(db_session):
    content = (
        "Oct 10 00:00:00 server sshd[1]: Accepted password for alice from 1.2.3.4 port 1 ssh2\n"
        "Oct 10 10:00:00 server sshd[1]: Accepted password for bob from 1.2.3.5 port 1 ssh2\n"
    )
    result = await ingest_evidence_file(
        db_session,
        evidence_file_id="ev-2",
        case_id="case-2",
        detected_format="syslog_auth",
        content=content,
        timezone_assumption="UTC",
    )
    await db_session.commit()

    assert result.records_parsed == 2
    assert result.gaps_detected == 1

    gaps = (await db_session.execute(select(ParsingGap))).scalars().all()
    assert len(gaps) == 1
    assert gaps[0].gap_start_line == 1
    assert gaps[0].gap_end_line == 2
    assert gaps[0].evidence_file_id == "ev-2"


@pytest.mark.asyncio
async def test_ingest_unknown_format_returns_zero_counts_without_error(db_session):
    result = await ingest_evidence_file(
        db_session,
        evidence_file_id="ev-3",
        case_id="case-3",
        detected_format="unknown",
        content="whatever content\n",
        timezone_assumption="UTC",
    )
    assert result.records_parsed == 0
    assert result.records_failed == 0
    assert result.gaps_detected == 0
    assert result.manual_estimate_seconds == 0.0


@pytest.mark.asyncio
async def test_ingest_reports_real_automated_time_and_labeled_manual_estimate(db_session):
    """Triage-time comparison fields: automated_seconds is a real (small,
    non-negative) measurement; manual_estimate_seconds is a deterministic,
    labeled assumption derived from the real line count -- never a
    fabricated or hardcoded demo number."""
    content = (
        "Oct 10 00:00:00 server sshd[1]: Accepted password for alice from 1.2.3.4 port 1 ssh2\n"
        "garbage line\n"
        "Oct 10 00:01:00 server sshd[1]: Accepted password for bob from 1.2.3.5 port 1 ssh2\n"
    )
    result = await ingest_evidence_file(
        db_session,
        evidence_file_id="ev-4",
        case_id="case-4",
        detected_format="syslog_auth",
        content=content,
        timezone_assumption="UTC",
    )

    assert result.automated_seconds >= 0
    total_lines = result.records_parsed + result.records_failed
    assert total_lines == 3
    assert result.manual_estimate_seconds == total_lines * 15
