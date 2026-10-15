"""Shared types for per-format parsers.

Every parser takes raw file content plus the two pieces of context the
ingestion service already has (the uploader's declared timezone assumption
and a reference year for formats without one -- see docs/TIMEZONE_POLICY.md)
and returns a flat list of `ParsedLine` results, one per *attempted* line.
Parsers never raise on bad input and never skip a line silently -- a line
either becomes a `ParsedRecord` or a `ParseErrorRecord`, both carrying the
original `line_number` and `raw_line` so every result is traceable back to
the source file (PROJECT_PLAN.md section 7).
"""
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ParsedRecord:
    line_number: int
    raw_line: str
    event_time_utc: datetime
    original_timezone: str
    event_type: str
    message: str
    severity: str = "info"
    source_ip: str | None = None
    user_or_actor: str | None = None
    extra: dict | None = None


@dataclass
class ParseErrorRecord:
    line_number: int
    raw_line: str
    reason: str


ParsedLine = ParsedRecord | ParseErrorRecord
