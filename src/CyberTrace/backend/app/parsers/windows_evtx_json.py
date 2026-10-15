"""Windows Event Log JSON export parser.

Format: output of `Get-WinEvent | ConvertTo-Json`, either a JSON array of
event objects or JSON-Lines, each with a `TimeCreated` ISO-8601 field, an
integer `Id`, a `LevelDisplayName`/`Level`, and a `Message`. Per
docs/TIMEZONE_POLICY.md: the ISO-8601 offset is used directly if present;
if `TimeCreated` is offset-naive, the uploader's declared
`timezone_assumption` is applied instead, matching the syslog case.

Unlike the line-oriented parsers, a single malformed *line* here means the
whole JSON-array document would fail to parse at all. To honor the "never
raise and skip" per-line contract even for this structured format, the
array form is parsed as one logical document (line_number=1 covering the
whole payload) when the array fails validation, while JSON-Lines input is
still evaluated one line/object at a time so a single bad line doesn't
sink the others.
"""
import json
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.parsers.base import ParseErrorRecord, ParsedLine, ParsedRecord

PARSER_NAME = "windows_evtx_json"

_LEVEL_TO_SEVERITY = {
    "critical": "critical",
    "error": "critical",
    "warning": "warning",
    "information": "info",
    "verbose": "info",
}


def _severity_from_level(level_name: str | None, level: int | None) -> str:
    if level_name:
        mapped = _LEVEL_TO_SEVERITY.get(level_name.strip().lower())
        if mapped:
            return mapped
    if level is not None:
        if level <= 2:
            return "critical"
        if level == 3:
            return "warning"
    return "info"


def _parse_event(
    obj: dict, line_number: int, raw_line: str, timezone_assumption: str
) -> ParsedLine:
    time_created = obj.get("TimeCreated")
    if not time_created or not isinstance(time_created, str):
        return ParseErrorRecord(
            line_number=line_number,
            raw_line=raw_line,
            reason="missing required field: TimeCreated",
        )

    text = time_created.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return ParseErrorRecord(
            line_number=line_number,
            raw_line=raw_line,
            reason="unrecognized timestamp format in TimeCreated",
        )

    if dt.tzinfo is not None:
        event_time_utc = dt.astimezone(ZoneInfo("UTC"))
        original_timezone = f"{dt.strftime('%z')} (embedded)"
    else:
        try:
            tz = ZoneInfo(timezone_assumption)
        except ZoneInfoNotFoundError:
            tz = ZoneInfo("UTC")
        event_time_utc = dt.replace(tzinfo=tz).astimezone(ZoneInfo("UTC"))
        original_timezone = f"{timezone_assumption} (assumed)"

    event_id = obj.get("Id")
    level_name = obj.get("LevelDisplayName")
    level = obj.get("Level")
    fallback_message = f"Event ID {event_id}" if event_id is not None else "Windows event"
    message = obj.get("Message") or fallback_message

    return ParsedRecord(
        line_number=line_number,
        raw_line=raw_line,
        event_time_utc=event_time_utc,
        original_timezone=original_timezone,
        event_type=f"windows_event_{event_id}" if event_id is not None else "windows_event",
        message=message,
        severity=_severity_from_level(level_name, level),
        source_ip=None,
        user_or_actor=obj.get("UserId"),
        extra={
            "Id": event_id,
            "LevelDisplayName": level_name,
            "ProviderName": obj.get("ProviderName"),
        },
    )


def parse(
    content: str,
    timezone_assumption: str = "UTC",
    reference_year: int | None = None,
) -> list[ParsedLine]:
    stripped = content.strip()
    if not stripped:
        return []

    # JSON array document: one Get-WinEvent | ConvertTo-Json export.
    if stripped.startswith("["):
        try:
            events = json.loads(stripped)
        except json.JSONDecodeError as exc:
            return [
                ParseErrorRecord(
                    line_number=1,
                    raw_line=content[:500],
                    reason=f"invalid JSON array: {exc}",
                )
            ]
        if not isinstance(events, list):
            return [
                ParseErrorRecord(
                    line_number=1, raw_line=content[:500], reason="expected a JSON array of events"
                )
            ]
        results: list[ParsedLine] = []
        for idx, obj in enumerate(events, start=1):
            if not isinstance(obj, dict):
                results.append(
                    ParseErrorRecord(
                        line_number=idx, raw_line=json.dumps(obj), reason="event entry is not a JSON object"
                    )
                )
                continue
            results.append(_parse_event(obj, idx, json.dumps(obj), timezone_assumption))
        return results

    # JSON-Lines: one JSON object per line.
    results = []
    for line_number, raw_line in enumerate(content.splitlines(), start=1):
        if not raw_line.strip():
            continue
        try:
            obj = json.loads(raw_line)
        except json.JSONDecodeError:
            results.append(
                ParseErrorRecord(
                    line_number=line_number, raw_line=raw_line, reason="invalid JSON on this line"
                )
            )
            continue
        if not isinstance(obj, dict):
            results.append(
                ParseErrorRecord(
                    line_number=line_number,
                    raw_line=raw_line,
                    reason="event entry is not a JSON object",
                )
            )
            continue
        results.append(_parse_event(obj, line_number, raw_line, timezone_assumption))

    return results
