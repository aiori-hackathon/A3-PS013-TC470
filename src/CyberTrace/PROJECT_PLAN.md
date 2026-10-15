# CyberTrace — Project Plan

Status: **DRAFT — awaiting approval. No application code has been written yet.**

CyberTrace is a small-team digital-forensics / incident-timeline tool. It ingests
raw log evidence in multiple formats, preserves the original files with
cryptographic hashes, normalizes events into a single UTC timeline, flags
anything it cannot parse (instead of dropping it), and lets an analyst search
the timeline and export a report. The workspace was confirmed empty before
writing this plan, so everything below is a from-scratch design, not a
refactor of existing code.

---

## 1. Design Direction (applies to every phase below)

This is meant to feel like a tool a small security team actually uses, not a
marketing site. Concretely:

- **Palette**: dark navy background (`#0B1220`/`#111827`), slate surfaces
  (`#1E293B`, `#334155`), muted blue primary accent (`#3B82F6`/`#60A5FA` used
  sparingly), restrained green for "verified / ok" states (`#22C55E`,
  used only for status, never decoration). No purple/pink gradients, no glow,
  no glassmorphism, no blur.
- **Typography**: one sans font (Inter or system-ui), modest heading sizes
  (page titles ~1.5–1.75rem, not hero-sized), monospace font for log/hash
  values.
- **Layout**: left sidebar nav (Dashboard, Cases, Evidence, Timeline, Parse
  Errors, Scenarios, Reports), top bar with case selector + user, content
  area dominated by tables and the timeline — not stat cards. A small number
  of summary numbers (e.g., counts) are allowed in a single compact strip,
  not a wall of cards.
- **Components**: one Button component (primary/secondary/destructive/ghost
  variants), one Table component (sortable headers, empty state, loading
  skeleton row, error row), one Badge component (status colors), one Card
  used only for grouping forms/details, one Modal/Drawer for record detail.
  Every button wired to a real handler — no dead UI.
- **Empty/loading/error states**: every data view defines all three
  explicitly (e.g., "No evidence uploaded yet", skeleton rows while loading,
  a red-bordered inline error with the backend error message/ID).
- **Synthetic data labeling**: a persistent `Badge` ("Synthetic scenario")
  on any case/record that originates from the three demo scenarios, plus a
  dedicated "Scenarios" page explaining what each one is and that it is not
  real incident data.
- **Accessibility**: semantic HTML landmarks, labeled form fields, visible
  focus states, sufficient color contrast against navy/slate, keyboard
  operable tables/menus, `aria-live` region for toast/error messages.
- **Logo/identity**: a simple inline SVG wordmark/monogram ("CT" in a
  rounded square, single accent color) used in the sidebar header and the
  PDF report cover — no external image assets needed.

---

## 1A. Making It Feel Authentic (Workflow-Driven, Not Decorative)

This section locks down three concrete product decisions so the tool reads
as something a real investigator would use, plus an anti-pattern checklist
to hold every later phase accountable to.

### A. The Timeline is the primary feature, not a dashboard

- The **Timeline page is the default landing view** after login (not a
  stat-card dashboard). The Dashboard page still exists but is intentionally
  small: case name, a compact strip of real counts (`records`, `parse
  errors`, `evidence files` — all pulled live from the DB, never hardcoded),
  and a link into the timeline. No charts, no gauges, no trend lines.
- The Timeline table has these columns, in this order, for every row:
  1. **Timestamp (UTC)** — the normalized `event_time_utc`, monospace.
  2. **Original timezone / offset** — what was parsed or assumed for that
     record (e.g., `America/New_York (assumed)` vs `+0000 (embedded)`),
     shown as a small secondary line under the timestamp so the UTC value
     is never presented without its provenance.
  3. **Source** — `source_ip` / host / actor, whatever the format provided.
  4. **Event type** — e.g., `auth_failure`, `http_request`.
  5. **Severity** — badge (info/warning/critical).
  6. **Parsing status** — a badge per row: `Parsed` (green) or, for rows
     that came from a file with nearby errors, a `Near parse gap` indicator
     linking to the relevant `parse_errors`/`parsing_gaps` entries.
  7. A row-click opens a detail drawer showing the full `raw_line`, the
     source evidence file (name + hash), and the line number — so every
     normalized row is traceable back to its original text.
- Required controls on the page: free-text search (`q`, matches
  message/raw_line), date range filter, event type filter, severity filter,
  source filter, column sort on timestamp — all backed by the real
  `GET /api/cases/{id}/timeline` query parameters, not client-side mock
  filtering.
- No decorative charts anywhere on this page. If a count is shown (e.g.,
  "214 records, 6 parse errors in range"), it is computed from the same
  query results being displayed, not a separate invented statistic.

### B. The Evidence page shows real, checkable facts

- Evidence list table columns: **original filename**, **detected format**,
  **file size**, **uploaded at (UTC)**, **SHA-256 hash** (monospace,
  truncated with a "copy full hash" button), **timezone assumption applied**,
  and a **verification status badge** (`Verified` / `Not yet verified` /
  `Hash mismatch`).
- A **"Verify integrity"** button per file calls
  `GET /api/evidence/{id}/verify`, which re-reads the stored file from disk,
  recomputes its SHA-256 live, and compares it to the hash recorded at
  upload time. The result (pass/fail, both hashes, timestamp of check) is
  shown inline — this is a real recomputation, not a cached flag.
- If verification fails (hash mismatch, file missing/unreadable), the UI
  shows a clear red error state with both hash values and the failure
  reason — this condition must be reachable in a test (e.g., a test that
  corrupts a stored file and asserts the API reports the mismatch), not
  just a hypothetical.
- Every `log_record` in the Timeline links back to its originating
  `evidence_files` entry (filename + hash) and exact `line_number`, and the
  evidence detail view lists how many records/errors came from that
  specific file — so "where did this fact come from" is always one click
  away.
- Original file download (`GET /api/evidence/{id}/download`) is always
  available, unmodified, next to the derived/normalized data.

### C. Limitations are first-class, visible UI, not a disclaimer

- A dedicated **"Parse Errors & Limitations"** view per case (combining the
  `parse_errors` and `parsing_gaps` data) is reachable from the sidebar and
  from a visible counter on the case page — never buried or omitted from
  navigation.
- For every evidence file, the UI states plainly, next to its metadata:
  the **timezone assumption applied** (e.g., "No timezone in source lines;
  assumed UTC"), any **clock-skew correction applied** (with the value and
  who/what set it), and counts of **malformed/unparsed lines** and
  **detected gaps** for that specific file — all derived from real
  `evidence_files`/`parse_errors`/`parsing_gaps` rows, not static text.
- Malformed records are rendered with their raw original text and the
  specific reason parsing failed (e.g., "unrecognized timestamp format",
  "missing required field: status_code") — never summarized away as just
  a generic "error" count.
- This view is what gets exported into the PDF/JSON reports' "Unparsed /
  anomalous records" section (see §10), so the same honesty is visible in
  the UI and in anything handed to a stakeholder.

### Anti-pattern checklist (binding for every phase)

- No fabricated metrics. If a number is displayed (e.g., "accuracy",
  "detection rate", "%"), it must be computed from real test results or
  real ingested data with a visible method — otherwise it is not shown at
  all. No invented marketing-style stats anywhere in the app.
- No button without a working handler. Before a phase is considered done,
  every new interactive element is exercised manually or by an automated
  test; nothing ships wired to a no-op or a `TODO`.
- No placeholder-only pages. A page is only added to navigation once it
  renders real data, a real empty state, or a real error state — not a
  static mockup.
- No AI chatbot or "AI-powered" feature bolted on for appearance — nothing
  in this plan includes one, and none should be added later just to look
  advanced.
- No one-shot code generation. Each phase in §12 is implemented, explained,
  and tested before the next starts, so every piece of code that ships is
  something that can be walked through and justified line by line.

---

## 2. Tech Stack

| Layer      | Choice |
|------------|--------|
| Frontend   | React 18 + TypeScript + Vite + Tailwind CSS |
| Backend    | Python 3.11+ + FastAPI + Pydantic v2 |
| Database   | PostgreSQL (local via Docker Compose for dev; schema is Supabase-compatible) |
| ORM/DB access | SQLAlchemy 2.0 (async) + Alembic migrations |
| Auth       | FastAPI's own JWT (password hashing via `passlib[bcrypt]`) — see open question #1 about whether to use Supabase Auth instead |
| File storage | Local filesystem under `backend/storage/evidence/` for dev, abstracted behind a small storage interface so it could point at Supabase Storage/S3 later |
| PDF export | `weasyprint` (HTML/CSS → PDF) — keeps report styling in plain HTML/CSS, matching the dashboard's own design system |
| Testing (backend) | `pytest`, `pytest-asyncio`, `httpx.AsyncClient` for API tests |
| Testing (frontend) | `vitest` + `@testing-library/react` |
| Lint/format | `ruff` + `black` (backend), `eslint` + `prettier` (frontend) |

No state-management library beyond React Query (TanStack Query) for
server-state caching — avoids Redux-style over-engineering for a CRUD-ish
dashboard.

---

## 3. High-Level Architecture

```
                     ┌─────────────────────────┐
                     │        Browser            │
                     │  React + TS + Tailwind     │
                     │  (dashboard SPA)           │
                     └───────────┬───────────────┘
                                 │ HTTPS / JSON (fetch via React Query)
                     ┌───────────▼───────────────┐
                     │       FastAPI backend      │
                     │  - auth                    │
                     │  - ingestion & parsers     │
                     │  - evidence/hash service   │
                     │  - timeline/search         │
                     │  - report export           │
                     │  - audit logging           │
                     └───────┬───────────┬────────┘
                             │           │
                 ┌───────────▼──┐   ┌────▼─────────────┐
                 │ PostgreSQL    │   │ Evidence storage   │
                 │ (cases,       │   │ (original files,   │
                 │ records,      │   │ content-addressed  │
                 │ errors,       │   │ by SHA-256)         │
                 │ reports,      │   └────────────────────┘
                 │ users, audit) │
                 └───────────────┘
```

Ingestion pipeline (per uploaded file):

```
upload → save raw bytes unmodified → compute SHA-256 → store EvidenceFile row
      → detect format (by filename/content sniffing, user can override)
      → run format-specific parser line-by-line
          ├─ success → normalized LogRecord (UTC timestamp, source fields, raw line kept)
          └─ failure → ParseError row (raw line, line number, reason) — never dropped silently
      → parsed LogRecords feed the case Timeline
      → ingestion summary returned: counts of parsed / failed / total, never swallowed
```

---

## 4. Folder Structure

```
CyberTrace/
├── PROJECT_PLAN.md
├── README.md
├── docker-compose.yml                # postgres + backend + frontend for local dev
├── .env.example
│
├── backend/
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── app/
│   │   ├── main.py                   # FastAPI app factory, CORS, routers
│   │   ├── config.py                 # settings via pydantic-settings
│   │   ├── db.py                     # async engine/session
│   │   ├── security.py               # hashing, JWT, password utils
│   │   ├── models/                   # SQLAlchemy models
│   │   │   ├── case.py
│   │   │   ├── evidence.py
│   │   │   ├── log_record.py
│   │   │   ├── parse_error.py
│   │   │   ├── report.py
│   │   │   ├── user.py
│   │   │   └── audit_log.py
│   │   ├── schemas/                  # Pydantic request/response models
│   │   ├── routers/
│   │   │   ├── auth.py
│   │   │   ├── cases.py
│   │   │   ├── evidence.py
│   │   │   ├── timeline.py
│   │   │   ├── parse_errors.py
│   │   │   ├── scenarios.py
│   │   │   └── reports.py
│   │   ├── parsers/
│   │   │   ├── base.py               # ParseResult, Parser protocol
│   │   │   ├── syslog_auth.py        # Linux auth.log / syslog RFC3164-ish
│   │   │   ├── apache_access.py      # Apache/Nginx combined log format
│   │   │   ├── windows_evtx_json.py  # Windows Event Log exported as JSON
│   │   │   └── registry.py           # format name -> parser lookup
│   │   ├── services/
│   │   │   ├── ingestion.py
│   │   │   ├── hashing.py
│   │   │   ├── timeline_search.py
│   │   │   ├── export_pdf.py
│   │   │   ├── export_csv.py
│   │   │   └── export_json.py
│   │   └── scenarios/                # synthetic scenario generators + fixtures
│   │       ├── scenario_1_ssh_bruteforce.py
│   │       ├── scenario_2_sql_injection.py
│   │       └── scenario_3_phishing_lateral_movement.py
│   ├── storage/evidence/             # gitignored, runtime evidence blobs
│   ├── sample_logs/                  # committed synthetic log files for the 3 scenarios
│   │   ├── scenario_1_ssh_bruteforce/
│   │   ├── scenario_2_sql_injection/
│   │   └── scenario_3_phishing_lateral_movement/
│   ├── migrations/                   # alembic versions
│   └── tests/
│       ├── unit/
│       │   ├── test_hashing.py
│       │   ├── test_syslog_parser.py
│       │   ├── test_apache_parser.py
│       │   ├── test_evtx_parser.py
│       │   └── test_timezone_normalization.py
│       ├── integration/
│       │   ├── test_ingestion_api.py
│       │   ├── test_timeline_search_api.py
│       │   ├── test_reports_api.py
│       │   └── test_auth.py
│       └── fixtures/
│           └── malformed_samples/    # deliberately broken lines per format
│
└── frontend/
    ├── package.json
    ├── tailwind.config.ts            # custom navy/slate/blue/green palette + type scale
    ├── vite.config.ts
    ├── src/
    │   ├── main.tsx
    │   ├── App.tsx
    │   ├── api/                      # typed fetch wrappers per resource
    │   ├── components/
    │   │   ├── ui/                   # Button, Table, Badge, Card, Modal, Skeleton
    │   │   ├── layout/                # Sidebar, Topbar, PageHeader
    │   │   └── timeline/              # TimelineList, TimelineFilters, RecordDetailDrawer
    │   ├── pages/
    │   │   ├── Dashboard.tsx
    │   │   ├── Cases.tsx
    │   │   ├── CaseDetail.tsx
    │   │   ├── EvidenceUpload.tsx
    │   │   ├── Timeline.tsx
    │   │   ├── ParseErrors.tsx
    │   │   ├── Scenarios.tsx
    │   │   ├── Reports.tsx
    │   │   └── Login.tsx
    │   ├── hooks/                     # React Query hooks
    │   ├── types/                     # shared TS types mirroring backend schemas
    │   └── styles/index.css
    └── tests/
        ├── components/
        └── pages/
```

---

## 5. Database Schema (PostgreSQL)

All timestamps stored as `timestamptz` (UTC). All primary keys `uuid`.

```sql
-- Users (minimal, single-role-aware auth)
users (
  id uuid PK,
  email text UNIQUE NOT NULL,
  password_hash text NOT NULL,
  role text NOT NULL DEFAULT 'analyst',   -- 'analyst' | 'admin'
  created_at timestamptz NOT NULL DEFAULT now()
)

-- A case groups evidence from one investigation (real or synthetic)
cases (
  id uuid PK,
  name text NOT NULL,
  description text,
  is_synthetic boolean NOT NULL DEFAULT false,   -- true for the 3 demo scenarios
  scenario_key text,                             -- e.g. 'ssh_bruteforce', null for real cases
  created_by uuid REFERENCES users(id),
  created_at timestamptz NOT NULL DEFAULT now()
)

-- One row per uploaded raw file. The file itself is never mutated.
evidence_files (
  id uuid PK,
  case_id uuid REFERENCES cases(id) ON DELETE CASCADE,
  original_filename text NOT NULL,
  detected_format text NOT NULL,          -- 'syslog_auth' | 'apache_access' | 'windows_evtx_json'
  declared_format text,                   -- format the uploader selected, if overridden
  sha256_hash text NOT NULL,              -- hex digest of raw bytes, computed on upload
  byte_size bigint NOT NULL,
  storage_path text NOT NULL,             -- content-addressed path under storage/evidence/
  uploaded_by uuid REFERENCES users(id),
  uploaded_at timestamptz NOT NULL DEFAULT now(),
  source_timezone_assumption text NOT NULL,  -- e.g. 'UTC' | 'America/New_York' — documented per file
  notes text
)

-- Normalized, successfully parsed events
log_records (
  id uuid PK,
  evidence_file_id uuid REFERENCES evidence_files(id) ON DELETE CASCADE,
  case_id uuid REFERENCES cases(id) ON DELETE CASCADE,
  line_number integer NOT NULL,
  raw_line text NOT NULL,                 -- original unmodified text, kept for evidence
  event_time_utc timestamptz NOT NULL,    -- normalized to UTC
  original_timezone text NOT NULL,        -- what we assumed/parsed, for traceability
  clock_skew_seconds integer,             -- applied correction, if any, else null
  source_ip text,
  user_or_actor text,
  event_type text,                        -- 'auth_failure','auth_success','http_request', etc.
  message text,                           -- human-readable normalized summary
  severity text,                          -- 'info' | 'warning' | 'critical' etc.
  extra jsonb                             -- format-specific extra fields
)

-- Anything the parser could not confidently interpret — never silently dropped
parse_errors (
  id uuid PK,
  evidence_file_id uuid REFERENCES evidence_files(id) ON DELETE CASCADE,
  case_id uuid REFERENCES cases(id) ON DELETE CASCADE,
  line_number integer NOT NULL,
  raw_line text NOT NULL,
  reason text NOT NULL,                   -- e.g. 'unrecognized timestamp format'
  parser_name text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
)

-- Detected ingestion gaps (e.g., large jump in line timestamps, truncated file)
parsing_gaps (
  id uuid PK,
  evidence_file_id uuid REFERENCES evidence_files(id) ON DELETE CASCADE,
  gap_start_line integer,
  gap_end_line integer,
  description text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
)

-- Exported report artifacts
reports (
  id uuid PK,
  case_id uuid REFERENCES cases(id) ON DELETE CASCADE,
  format text NOT NULL,                   -- 'pdf' | 'csv' | 'json'
  storage_path text NOT NULL,
  generated_by uuid REFERENCES users(id),
  generated_at timestamptz NOT NULL DEFAULT now()
)

-- Append-only audit trail of security-relevant actions
audit_log (
  id uuid PK,
  user_id uuid REFERENCES users(id),
  action text NOT NULL,                   -- 'login','upload_evidence','export_report', etc.
  target_type text,
  target_id uuid,
  detail jsonb,
  ip_address text,
  created_at timestamptz NOT NULL DEFAULT now()
)
```

Indexes planned: `log_records(case_id, event_time_utc)` for timeline queries,
`log_records` full-text/`ilike` index on `message`/`raw_line` for search,
`evidence_files(sha256_hash)` unique-ish lookup for integrity re-verification.

---

## 6. API Endpoints (FastAPI)

Auth (`/api/auth`):
- `POST /api/auth/register` — create analyst account (admin-only in practice; open question #1)
- `POST /api/auth/login` — returns JWT
- `GET  /api/auth/me`

Cases (`/api/cases`):
- `GET    /api/cases` — list cases (filter by `is_synthetic`)
- `POST   /api/cases` — create a real case
- `GET    /api/cases/{case_id}` — detail + counts (records, errors, evidence files)
- `DELETE /api/cases/{case_id}`

Evidence (`/api/cases/{case_id}/evidence`):
- `POST /api/cases/{case_id}/evidence` — multipart upload; computes SHA-256,
  stores raw file, kicks off parsing, returns ingestion summary
  (`records_parsed`, `records_failed`, `gaps_detected`, `sha256`)
- `GET  /api/cases/{case_id}/evidence` — list evidence files with hash/size/format
- `GET  /api/evidence/{evidence_id}/download` — download original raw file
- `GET  /api/evidence/{evidence_id}/verify` — recompute SHA-256 of stored file
  and compare to recorded hash (integrity check on demand)

Timeline (`/api/cases/{case_id}/timeline`):
- `GET /api/cases/{case_id}/timeline` — paginated, filterable
  (`q` text search, `start`, `end`, `event_type`, `severity`, `source_ip`)
- `GET /api/log-records/{record_id}` — full record detail incl. raw line

Parse errors / gaps (`/api/cases/{case_id}/parse-errors`, `/parsing-gaps`):
- `GET /api/cases/{case_id}/parse-errors` — paginated list, never hidden from the UI
- `GET /api/cases/{case_id}/parsing-gaps`

Scenarios (`/api/scenarios`):
- `GET  /api/scenarios` — list the 3 synthetic scenario definitions
- `POST /api/scenarios/{key}/load` — (admin) generates the case + ingests its
  bundled sample logs, so the demo data is reproducible rather than hand-seeded

Reports (`/api/cases/{case_id}/reports`):
- `POST /api/cases/{case_id}/reports?format=pdf|csv|json` — generate report
- `GET  /api/cases/{case_id}/reports` — list previously generated reports
- `GET  /api/reports/{report_id}/download`

All mutating endpoints require auth and write to `audit_log`.

---

## 7. Log Formats to Ingest (≥2 required — planning 3)

1. **Linux syslog / `auth.log`** (SSH login attempts, sudo events) — classic
   RFC3164-ish `"Mon DD HH:MM:SS host process[pid]: message"`. No year or
   timezone in the line itself, so the parser must document and apply an
   assumed year/timezone, which is exactly the clock-skew/timezone case the
   requirements ask us to document.
2. **Apache/Nginx combined access log** — `"%h %l %u %t \"%r\" %>s %b"` with
   an explicit `[day/Mon/year:HH:MM:SS +ZZZZ]` offset — good contrast case
   since it *does* carry explicit UTC offset per line.
3. **Windows Event Log exported as JSON** (e.g., `Get-WinEvent | ConvertTo-Json`
   shape) — `TimeCreated` as ISO-8601, ids/levels as integers — a structured
   format contrasted against the two line-oriented text formats above.

Each parser returns, per line, either a normalized record or a `ParseError`
with the raw line and a reason (e.g., unparseable timestamp, missing
required field, invalid JSON). Parsers never raise and skip; the ingestion
service wraps each line individually.

**Timezone/clock-skew policy (to be written into `docs/TIMEZONE_POLICY.md`
and enforced in code):**
- Every `evidence_files` row requires an explicit `source_timezone_assumption`
  chosen by the uploader (default `UTC`, selectable at upload time) for
  formats without embedded offsets (syslog).
- Formats with embedded offsets (Apache, Windows ISO-8601) use the embedded
  offset directly; the uploader's assumption is recorded but not applied.
- A per-case optional `clock_skew_seconds` correction can be supplied (e.g.,
  "this host's clock was 3 minutes fast") and is applied at normalization
  time, with the applied value stored per record for traceability — never
  silently baked in without a record of it.
- All of this is surfaced in the UI next to each evidence file and each
  timeline record ("Interpreted as UTC-5, +0s skew applied") so a reviewer
  can see the assumption, not just the result.

**Malformed records / gaps (requirement 5):**
- Per-line failures → `parse_errors` table, shown in a dedicated "Parse
  Errors" tab per case (not hidden, not just a console log).
- Gap detection heuristic: if consecutive successfully-parsed timestamps in
  a file jump by more than a configurable threshold, or if the file appears
  truncated (e.g., ends mid-line), record a `parsing_gaps` row describing the
  suspected gap/truncation with the surrounding line numbers.
- Ingestion response always reports `records_parsed`, `records_failed`,
  `gaps_detected` — the UI must show this summary immediately after upload,
  not just a generic "success" toast.

---

## 8. Evidence Preservation

- Raw uploaded bytes are written once to
  `storage/evidence/<sha256>/<original_filename>` and never modified afterward.
- SHA-256 is computed immediately on upload (streaming, not loaded fully for
  very large files) and stored in `evidence_files.sha256_hash`.
- `GET /api/evidence/{id}/verify` recomputes the hash on demand so an analyst
  can confirm the stored file still matches what was recorded — a basic
  chain-of-custody integrity check, surfaced in the Evidence page as a
  "Verify integrity" button with a clear pass/fail result.
- Original file download is always available unmodified alongside the
  normalized records derived from it.

---

## 9. Three Synthetic Incident Scenarios

All three are clearly labeled `is_synthetic = true` with a `scenario_key`,
shown with a persistent "Synthetic scenario" badge everywhere they appear,
and documented on a dedicated Scenarios page. Sample logs are committed
under `backend/sample_logs/` and are loaded via `POST /api/scenarios/{key}/load`
so they're reproducible rather than mystery seed data.

1. **`ssh_bruteforce`** — repeated failed SSH logins from a small set of IPs
   against `auth.log`, culminating in one successful login — includes a few
   corrupted/truncated lines to exercise parse-error handling.
2. **`sql_injection_probe`** — Apache/Nginx access log showing a scanner
   probing query parameters with SQLi payloads, mixed with normal traffic,
   including a couple of lines with malformed status codes/missing fields.
3. **`phishing_lateral_movement`** — Windows Event Log JSON export showing
   an initial suspicious logon, then a new-process-creation and a new-user
   or privilege-escalation event shortly after — includes a deliberate
   mid-sequence timestamp/clock-skew inconsistency to exercise the
   skew-handling UI.

---

## 10. Report Export (PDF / CSV / JSON)

- **JSON**: full case export — case metadata, evidence file metadata (incl.
  hashes), all timeline records, all parse errors/gaps. This is the
  "ground truth" machine-readable export.
- **CSV**: flattened timeline records (one row per `log_record`) plus a
  separate CSV for parse errors, zipped together — chosen over a single
  mixed CSV so each file has a consistent column set.
- **PDF**: human-readable incident report generated via HTML template →
  WeasyPrint — cover page (case name, generated date, evidence hash list),
  summary counts, the timeline, and an explicit "Unparsed / anomalous
  records" section so gaps are visible in the delivered report, not just
  the UI.

---

## 11. Security Controls

- Password hashing with bcrypt; JWT access tokens, short expiry + refresh.
- File upload validation: extension/content-type allow-list, max size limit,
  streamed hashing to avoid memory blow-up.
- Parameterized queries only (SQLAlchemy ORM/Core — no raw string SQL).
- CORS restricted to the configured frontend origin.
- Rate limiting on `/api/auth/login` (basic in-memory or `slowapi`) to blunt
  brute-force attempts against the tool itself.
- Audit log for login, upload, export, and delete actions, viewable by admins.
- Secrets (DB URL, JWT secret) via environment variables / `.env`, never
  committed; `.env.example` provided.
- Dependency versions pinned in `pyproject.toml`/`package.json`.
- Backend input validation entirely through Pydantic schemas; no trusting of
  client-declared format without server-side content sniffing as a cross-check.

---

## 12. Implementation Phases

Built and verified one feature at a time, per your development approach;
each phase ends with passing tests before moving on.

1. **Scaffolding** — repo structure, Docker Compose (Postgres), FastAPI app
   skeleton with health check, Vite+React+Tailwind skeleton with the design
   system (colors, Button/Table/Badge components), basic routing/sidebar shell.
2. **Auth** — users table, register/login/me, JWT middleware, protected
   route wrapper on frontend, Login page.
3. **Cases + Evidence upload + hashing** — case CRUD, evidence upload
   endpoint with SHA-256, evidence list/download/verify UI.
4. **Parsers (syslog, Apache, Windows JSON)** — parser modules + unit tests
   with good and malformed fixtures, ingestion service wiring parse errors
   and gaps, ingestion summary surfaced in UI.
5. **Timeline + search** — timeline query endpoint with filters/pagination,
   Timeline page with search bar, filters, record detail drawer.
6. **Parse Errors / Gaps UI** — dedicated page, counts surfaced on case
   detail and dashboard.
7. **Synthetic scenarios** — three scenario generators/fixtures, load
   endpoint, Scenarios page with clear labeling.
8. **Reports export** — JSON/CSV/PDF generation endpoints + Reports page.
9. **Security hardening pass** — rate limiting, audit log wiring/UI, upload
   validation review, dependency/CORS review.
10. **Test completion + polish** — fill remaining unit/integration/frontend
    test gaps, accessibility pass, empty/loading/error state review across
    all pages.

---

## 13. Test Strategy

**Backend (pytest):**
- Unit tests per parser: valid line → expected normalized fields; malformed
  line → `ParseError` with expected reason, never an unhandled exception.
- Unit tests for timezone normalization: syslog without offset uses the
  declared assumption; Apache/Windows embedded offsets are respected; clock
  skew correction is applied and recorded.
- Unit tests for hashing service: known bytes → known SHA-256 digest;
  verify-endpoint logic detects a deliberately corrupted stored file.
- Integration tests (httpx `AsyncClient` against the FastAPI app with a test
  Postgres DB or SQLite-compatible test DB): upload → ingestion summary
  counts match fixture expectations; timeline search filters behave
  correctly; report export endpoints return well-formed PDF/CSV/JSON;
  auth flow (register/login/me, rejected bad credentials, protected routes
  reject missing/invalid JWT).
- Scenario tests: loading each of the 3 scenarios produces the expected
  non-zero `records_parsed`, `records_failed`, and `gaps_detected` counts.

**Frontend (vitest + React Testing Library):**
- Component tests for Button/Table/Badge (variants render, empty/loading/
  error states render correctly).
- Page-level tests with mocked API responses: Timeline page renders records,
  search input triggers a query, Parse Errors page shows errors, Evidence
  page shows hash and a working "Verify integrity" button, Scenarios page
  labels synthetic data.

**What "done" means for this task**: tests are run and their actual pass/fail
output is reported to you — nothing is marked complete without a real test
run shown.

---

## 14. Open Questions / Decisions Needed Before Coding Starts

1. **Auth scope** — do you want real username/password auth from day one
   (my default plan), or is a single shared admin login acceptable for this
   stage, or should I integrate Supabase Auth specifically (not just
   Supabase Postgres)?
2. **Database**: local Postgres via Docker Compose for development (my
   default), or do you already have a Supabase project you want me to point
   this at directly?
3. **PDF library**: WeasyPrint (HTML/CSS based, my default) requires some
   native system libraries (Pango/Cairo) — acceptable, or would you prefer
   `reportlab` (pure Python, more manual layout code) instead?
4. Any preference on the **third log format** — I proposed Windows Event Log
   JSON export for format diversity (structured vs. the two line-oriented
   formats); happy to swap for something else (e.g., firewall/CSV logs) if
   you have a specific one in mind.

---

Once you approve this plan (and answer the open questions above, or confirm
the stated defaults), I will proceed with Phase 1 (scaffolding) and report
back with real command output before moving to Phase 2. Per the design
direction, Phase 1 will stand up the actual visual identity (navy/slate/blue/
green palette, Button/Table/Badge components, sidebar shell) rather than a
generic placeholder UI, so you can sanity-check the look and feel early.
