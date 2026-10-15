"""Apache/Nginx combined access log parser.

Format: '%h %l %u %t "%r" %>s %b' with an explicit
`[day/Mon/year:HH:MM:SS +ZZZZ]` offset per line. Per
docs/TIMEZONE_POLICY.md, the embedded offset is used directly to compute
`event_time_utc` -- the uploader's timezone assumption is recorded but not
applied here, since the source already states the offset.
"""
import re
from datetime import datetime, timezone

from app.parsers.base import ParseErrorRecord, ParsedLine, ParsedRecord

PARSER_NAME = "apache_access"

_LINE_RE = re.compile(
    r'^(?P<ip>\S+)\s+\S+\s+(?P<user>\S+)\s+'
    r'\[(?P<ts>[^\]]+)\]\s+'
    r'"(?P<method>[A-Z]+)\s+(?P<path>\S+)(?:\s+HTTP/[\d.]+)?"\s+'
    r'(?P<status>\d{3})\s+(?P<size>\S+)'
)


def _severity_for_status(status_code: int) -> str:
    if status_code >= 500:
        return "critical"
    if status_code >= 400:
        return "warning"
    return "info"


def parse(
    content: str,
    timezone_assumption: str = "UTC",
    reference_year: int | None = None,
) -> list[ParsedLine]:
    results: list[ParsedLine] = []
    for line_number, raw_line in enumerate(content.splitlines(), start=1):
        if not raw_line.strip():
            continue

        match = _LINE_RE.match(raw_line)
        if not match:
            results.append(
                ParseErrorRecord(
                    line_number=line_number,
                    raw_line=raw_line,
                    reason="unrecognized Apache/Nginx combined log line format",
                )
            )
            continue

        ts_text = match.group("ts")
        try:
            dt = datetime.strptime(ts_text, "%d/%b/%Y:%H:%M:%S %z")
        except ValueError:
            results.append(
                ParseErrorRecord(
                    line_number=line_number,
                    raw_line=raw_line,
                    reason="unrecognized timestamp format",
                )
            )
            continue

        event_time_utc = dt.astimezone(timezone.utc)
        offset = dt.strftime("%z")
        status_code = int(match.group("status"))
        size = match.group("size")

        results.append(
            ParsedRecord(
                line_number=line_number,
                raw_line=raw_line,
                event_time_utc=event_time_utc,
                original_timezone=f"{offset} (embedded)",
                event_type="http_request",
                message=f'{match.group("method")} {match.group("path")} -> {status_code}',
                severity=_severity_for_status(status_code),
                source_ip=match.group("ip"),
                user_or_actor=match.group("user") if match.group("user") != "-" else None,
                extra={
                    "method": match.group("method"),
                    "path": match.group("path"),
                    "status": status_code,
                    "bytes": None if size == "-" else int(size),
                },
            )
        )

    return results
