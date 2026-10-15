"""Linux syslog / auth.log parser.

Format: "Mon DD HH:MM:SS host process[pid]: message" (RFC3164-ish). No year
or timezone embedded, so per docs/TIMEZONE_POLICY.md the uploader's
`source_timezone_assumption` and a reference year (defaulting to the
current year) are applied to every parsed line -- never auto-detected.
"""
import re
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.parsers.base import ParseErrorRecord, ParsedLine, ParsedRecord

PARSER_NAME = "syslog_auth"

_LINE_RE = re.compile(
    r"^(?P<ts>[A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+"
    r"(?P<host>\S+)\s+"
    r"(?P<process>[\w./-]+)(?:\[(?P<pid>\d+)\])?:\s*"
    r"(?P<message>.*)$"
)

_SSH_FAILED_RE = re.compile(
    r"Failed password for (?:invalid user )?(?P<user>\S+) from (?P<ip>[\d.:a-fA-F]+)"
)
_SSH_ACCEPTED_RE = re.compile(
    r"Accepted (?:password|publickey) for (?P<user>\S+) from (?P<ip>[\d.:a-fA-F]+)"
)
_SUDO_RE = re.compile(r"^\s*(?P<user>\S+)\s*:.*COMMAND=")


def _classify(process: str, message: str) -> tuple[str, str, str | None, str | None]:
    """Returns (event_type, severity, source_ip, user_or_actor)."""
    if "sshd" in process:
        m = _SSH_FAILED_RE.search(message)
        if m:
            return "auth_failure", "warning", m.group("ip"), m.group("user")
        m = _SSH_ACCEPTED_RE.search(message)
        if m:
            return "auth_success", "info", m.group("ip"), m.group("user")
        return "ssh_event", "info", None, None
    if "sudo" in process:
        m = _SUDO_RE.search(message)
        user = m.group("user") if m else None
        return "sudo_command", "info", None, user
    return "syslog_event", "info", None, None


def parse(
    content: str,
    timezone_assumption: str = "UTC",
    reference_year: int | None = None,
) -> list[ParsedLine]:
    year = reference_year or datetime.now().year
    try:
        tz = ZoneInfo(timezone_assumption)
    except ZoneInfoNotFoundError:
        tz = ZoneInfo("UTC")

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
                    reason="unrecognized syslog line format",
                )
            )
            continue

        ts_text = f"{match.group('ts')} {year}"
        try:
            naive_dt = datetime.strptime(ts_text, "%b %d %H:%M:%S %Y")
        except ValueError:
            results.append(
                ParseErrorRecord(
                    line_number=line_number,
                    raw_line=raw_line,
                    reason="unrecognized timestamp format",
                )
            )
            continue

        local_dt = naive_dt.replace(tzinfo=tz)
        event_time_utc = local_dt.astimezone(ZoneInfo("UTC"))

        process = match.group("process")
        message = match.group("message")
        event_type, severity, source_ip, user_or_actor = _classify(process, message)

        results.append(
            ParsedRecord(
                line_number=line_number,
                raw_line=raw_line,
                event_time_utc=event_time_utc,
                original_timezone=f"{timezone_assumption} (assumed)",
                event_type=event_type,
                message=message,
                severity=severity,
                source_ip=source_ip,
                user_or_actor=user_or_actor,
                extra={"host": match.group("host"), "process": process, "pid": match.group("pid")},
            )
        )

    return results
