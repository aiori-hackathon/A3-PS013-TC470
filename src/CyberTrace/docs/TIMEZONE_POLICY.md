# Timezone & Clock-Skew Policy

This document is referenced from `PROJECT_PLAN.md` section 7 and will be
enforced by the parsers implemented in Phase 4.

## Principle

Every timestamp displayed or stored in CyberTrace's normalized timeline
(`log_records.event_time_utc`) is UTC. However, UTC conversion requires an
assumption whenever the source log does not carry an explicit UTC offset.
CyberTrace never hides that assumption — it is recorded per evidence file
and shown next to every affected timestamp in the UI.

## Per-format handling

| Format | Timestamp in source | Policy |
|---|---|---|
| Linux syslog / `auth.log` | No year, no timezone (`"Mon DD HH:MM:SS"`) | Uploader must select a `source_timezone_assumption` (default `UTC`) and, if the file spans a year boundary or the host clock year is otherwise ambiguous, confirm the assumed year. This assumption is stored on `evidence_files.source_timezone_assumption` and copied onto each derived `log_records.original_timezone`. |
| Apache/Nginx combined access log | Explicit offset per line (`[10/Oct/2026:13:55:36 +0000]`) | The embedded offset is used directly to compute `event_time_utc`. The uploader's timezone assumption is recorded but **not** applied, since the source already states the offset — this is intentional and documented in the UI so the two cases aren't confused. |
| Windows Event Log JSON export | ISO-8601 `TimeCreated` (typically already UTC or with an offset) | The ISO-8601 offset (if present) is used directly; if the field is offset-naive, the uploader's declared assumption is applied, same as the syslog case. |

## Clock skew

If an analyst knows a given host's clock was running fast or slow (e.g.,
confirmed via another authoritative time source during the investigation),
they can supply a `clock_skew_seconds` correction for an evidence file.
This value is:

- applied at normalization time, added/subtracted from each record's
  computed UTC timestamp,
- stored per-record (`log_records.clock_skew_seconds`) so a reviewer can
  see exactly what correction was applied to which record, and
- never applied silently — the UI always shows "Interpreted as UTC-5, +180s
  skew applied" or equivalent, not just the final corrected value.

## What this policy does NOT do

- It does not attempt to auto-detect timezone from IP geolocation, system
  locale, or any heuristic — all timezone assumptions are either
  machine-parsed from the source format or explicitly supplied by a human
  analyst.
- It does not silently correct "obviously wrong" timestamps. If a record's
  timestamp looks anomalous, that is surfaced via the gap-detection
  mechanism (see `PROJECT_PLAN.md` section 7, `parsing_gaps` table), not
  silently patched.
