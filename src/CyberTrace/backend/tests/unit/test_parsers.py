"""Unit tests for the per-format parsers (syslog_auth, apache_access,
windows_evtx_json): valid records, malformed input, timestamp handling,
and that parsers never raise/skip -- every line becomes exactly one
ParsedRecord or ParseErrorRecord."""
from datetime import timezone

from app.parsers import apache_access, syslog_auth, windows_evtx_json
from app.parsers.base import ParseErrorRecord, ParsedRecord


# ---------------------------------------------------------------------------
# syslog_auth
# ---------------------------------------------------------------------------


def test_syslog_parses_valid_ssh_failure_and_success():
    content = (
        "Oct 10 13:55:36 server sshd[1234]: Failed password for root from 10.0.0.5 port 4444 ssh2\n"
        "Oct 10 13:56:01 server sshd[1234]: Accepted password for alice from 10.0.0.9 port 22 ssh2\n"
    )
    results = syslog_auth.parse(content, timezone_assumption="UTC", reference_year=2026)

    assert len(results) == 2
    assert all(isinstance(r, ParsedRecord) for r in results)

    failure, success = results
    assert failure.event_type == "auth_failure"
    assert failure.severity == "warning"
    assert failure.source_ip == "10.0.0.5"
    assert failure.user_or_actor == "root"
    assert failure.line_number == 1
    assert failure.raw_line.startswith("Oct 10 13:55:36")

    assert success.event_type == "auth_success"
    assert success.user_or_actor == "alice"
    assert success.source_ip == "10.0.0.9"

    # Timestamp is normalized to UTC using the supplied reference year.
    assert failure.event_time_utc.tzinfo is not None
    assert failure.event_time_utc.year == 2026
    assert failure.event_time_utc.month == 10
    assert failure.event_time_utc.day == 10
    assert failure.original_timezone == "UTC (assumed)"


def test_syslog_applies_timezone_assumption():
    content = "Oct 10 13:55:36 server sshd[1]: Failed password for root from 1.2.3.4 port 1 ssh2\n"
    results = syslog_auth.parse(content, timezone_assumption="America/New_York", reference_year=2026)

    record = results[0]
    assert isinstance(record, ParsedRecord)
    # 13:55:36 Eastern (UTC-4 in October) -> 17:55:36 UTC.
    assert record.event_time_utc.astimezone(timezone.utc).hour == 17
    assert record.original_timezone == "America/New_York (assumed)"


def test_syslog_records_parse_error_for_malformed_line():
    content = "this is not a valid syslog line at all\n"
    results = syslog_auth.parse(content, timezone_assumption="UTC", reference_year=2026)

    assert len(results) == 1
    assert isinstance(results[0], ParseErrorRecord)
    assert results[0].line_number == 1
    assert "syslog" in results[0].reason.lower()


def test_syslog_never_skips_a_line_mixed_valid_and_malformed():
    content = (
        "Oct 10 13:55:36 server sshd[1]: Failed password for root from 1.2.3.4 port 1 ssh2\n"
        "garbage line without timestamp\n"
        "Oct 10 13:56:00 server sshd[1]: Accepted password for bob from 5.6.7.8 port 2 ssh2\n"
    )
    results = syslog_auth.parse(content, timezone_assumption="UTC", reference_year=2026)

    assert len(results) == 3
    assert isinstance(results[0], ParsedRecord)
    assert isinstance(results[1], ParseErrorRecord)
    assert results[1].line_number == 2
    assert isinstance(results[2], ParsedRecord)


# ---------------------------------------------------------------------------
# apache_access
# ---------------------------------------------------------------------------


def test_apache_parses_valid_line_with_embedded_offset():
    line = '127.0.0.1 - - [10/Oct/2026:13:55:36 +0000] "GET /index.html HTTP/1.1" 200 1024\n'
    results = apache_access.parse(line, timezone_assumption="UTC")

    assert len(results) == 1
    record = results[0]
    assert isinstance(record, ParsedRecord)
    assert record.event_type == "http_request"
    assert record.source_ip == "127.0.0.1"
    assert record.severity == "info"
    assert record.extra["status"] == 200
    assert record.extra["bytes"] == 1024
    assert record.original_timezone == "+0000 (embedded)"
    assert record.event_time_utc.year == 2026
    assert record.event_time_utc.hour == 13


def test_apache_uses_embedded_offset_not_uploader_assumption():
    # Declared assumption is UTC but the embedded offset is -0500; the
    # embedded offset must win per docs/TIMEZONE_POLICY.md.
    line = '10.0.0.1 - - [10/Oct/2026:10:00:00 -0500] "GET / HTTP/1.1" 200 10\n'
    results = apache_access.parse(line, timezone_assumption="UTC")

    record = results[0]
    assert isinstance(record, ParsedRecord)
    assert record.event_time_utc.hour == 15  # 10:00 -0500 == 15:00 UTC
    assert record.original_timezone == "-0500 (embedded)"


def test_apache_severity_maps_to_status_code():
    lines = (
        '1.1.1.1 - - [10/Oct/2026:00:00:00 +0000] "GET / HTTP/1.1" 500 10\n'
        '1.1.1.1 - - [10/Oct/2026:00:00:01 +0000] "GET / HTTP/1.1" 404 10\n'
        '1.1.1.1 - - [10/Oct/2026:00:00:02 +0000] "GET / HTTP/1.1" 200 10\n'
    )
    results = apache_access.parse(lines, timezone_assumption="UTC")
    assert [r.severity for r in results] == ["critical", "warning", "info"]


def test_apache_records_parse_error_for_malformed_line():
    results = apache_access.parse("not an apache log line\n", timezone_assumption="UTC")
    assert len(results) == 1
    assert isinstance(results[0], ParseErrorRecord)



# ---------------------------------------------------------------------------
# windows_evtx_json
# ---------------------------------------------------------------------------


def test_windows_json_array_parses_valid_events():
    content = (
        '[{"TimeCreated": "2026-10-10T13:55:36Z", "Id": 4625, '
        '"LevelDisplayName": "Warning", "Message": "An account failed to log on"}]'
    )
    results = windows_evtx_json.parse(content, timezone_assumption="UTC")

    assert len(results) == 1
    record = results[0]
    assert isinstance(record, ParsedRecord)
    assert record.event_type == "windows_event_4625"
    assert record.severity == "warning"
    assert record.message == "An account failed to log on"
    assert record.event_time_utc.year == 2026
    assert record.original_timezone == "+0000 (embedded)"


def test_windows_json_lines_parses_valid_events():
    content = (
        '{"TimeCreated": "2026-10-10T13:55:36Z", "Id": 4624, "LevelDisplayName": "Information"}\n'
        '{"TimeCreated": "2026-10-10T13:56:00Z", "Id": 4625, "LevelDisplayName": "Error"}\n'
    )
    results = windows_evtx_json.parse(content, timezone_assumption="UTC")

    assert len(results) == 2
    assert all(isinstance(r, ParsedRecord) for r in results)
    assert results[0].severity == "info"
    assert results[1].severity == "critical"


def test_windows_json_applies_timezone_assumption_when_offset_naive():
    content = '[{"TimeCreated": "2026-10-10T13:55:36", "Id": 1}]'
    results = windows_evtx_json.parse(content, timezone_assumption="America/New_York")

    record = results[0]
    assert isinstance(record, ParsedRecord)
    assert record.original_timezone == "America/New_York (assumed)"
    assert record.event_time_utc.hour == 17  # 13:55 EDT -> 17:55 UTC


def test_windows_json_records_parse_error_for_missing_timecreated():
    content = '[{"Id": 1, "Message": "no timestamp here"}]'
    results = windows_evtx_json.parse(content, timezone_assumption="UTC")

    assert len(results) == 1
    assert isinstance(results[0], ParseErrorRecord)
    assert "TimeCreated" in results[0].reason


def test_windows_json_invalid_array_reports_single_parse_error():
    results = windows_evtx_json.parse("[ this is not valid json", timezone_assumption="UTC")
    assert len(results) == 1
    assert isinstance(results[0], ParseErrorRecord)


def test_windows_json_lines_isolates_malformed_line():
    content = (
        '{"TimeCreated": "2026-10-10T13:55:36Z", "Id": 1}\n'
        "not json at all\n"
        '{"TimeCreated": "2026-10-10T13:56:00Z", "Id": 2}\n'
    )
    results = windows_evtx_json.parse(content, timezone_assumption="UTC")

    assert len(results) == 3
    assert isinstance(results[0], ParsedRecord)
    assert isinstance(results[1], ParseErrorRecord)
    assert isinstance(results[2], ParsedRecord)

    assert results[0].line_number == 1
