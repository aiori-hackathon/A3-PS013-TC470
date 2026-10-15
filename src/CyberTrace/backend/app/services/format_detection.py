"""Lightweight content-based format detection for uploaded evidence files.

Used so the server does not blindly trust a client-declared format
(PROJECT_PLAN.md section 11: "no trusting of client-declared format without
server-side content sniffing as a cross-check"). Detection is deliberately
simple and line-oriented -- it looks at the first few non-empty lines.
"""
import json

SUPPORTED_FORMATS = {"syslog_auth", "apache_access", "windows_evtx_json"}


def detect_format(sample_text: str) -> str:
    """Best-effort detection of one of the supported log formats from a text
    sample (typically the first ~64KB of the uploaded file, decoded as
    UTF-8 with errors replaced). Returns 'unknown' if nothing matches --
    callers should still accept the upload and let the parser report
    per-line errors rather than reject the whole file outright.
    """
    lines = [line for line in sample_text.splitlines() if line.strip()]
    if not lines:
        return "unknown"

    first_line = lines[0].strip()

    # Windows Event Log JSON export: either a JSON array of objects or
    # JSON-Lines, each with a "TimeCreated" field (from Get-WinEvent |
    # ConvertTo-Json shape referenced in PROJECT_PLAN.md section 7).
    stripped_sample = sample_text.strip()
    if stripped_sample.startswith("[") or stripped_sample.startswith("{"):
        try:
            parsed = json.loads(first_line) if first_line.startswith("{") else None
            if parsed is None and stripped_sample.startswith("["):
                parsed_all = json.loads(stripped_sample)
                parsed = parsed_all[0] if isinstance(parsed_all, list) and parsed_all else None
            if isinstance(parsed, dict) and "TimeCreated" in parsed:
                return "windows_evtx_json"
        except (json.JSONDecodeError, IndexError):
            pass

    # Apache/Nginx combined access log: starts with an IP/host, contains a
    # bracketed timestamp and a quoted HTTP request line.
    if " - - [" in first_line or (" [" in first_line and '"' in first_line and " HTTP/" in first_line):
        return "apache_access"

    # Linux syslog / auth.log: "Mon DD HH:MM:SS host process[pid]: message"
    # First token is a 3-letter month abbreviation.
    month_abbrevs = {
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
    }
    first_token = first_line.split(" ", 1)[0] if first_line else ""
    if first_token in month_abbrevs:
        return "syslog_auth"

    return "unknown"
