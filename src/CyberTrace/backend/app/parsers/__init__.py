"""Per-format log parsers, dispatched by `evidence_files.detected_format`.

Each entry's `parse` function has the signature
`parse(content, timezone_assumption, reference_year) -> list[ParsedLine]`
(see app.parsers.base) so the ingestion service can call any of them
uniformly, with no per-format special-casing.
"""
from app.parsers import apache_access, syslog_auth, windows_evtx_json

PARSERS = {
    "syslog_auth": syslog_auth.parse,
    "apache_access": apache_access.parse,
    "windows_evtx_json": windows_evtx_json.parse,
}
