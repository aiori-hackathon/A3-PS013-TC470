# CyberTrace — Progress Checklist

Last updated: 2026-10-15 — hosting preparation and interface polish added;
automated verification passed.
Tracks actual implementation status against
`PROJECT_PLAN.md` section 12 (Implementation Phases). Nothing below is
marked done without a real, reproducible test or manual verification.

## Phase 1 — Scaffolding ✅ COMPLETE

- [x] Repo folder structure (`backend/`, `frontend/`, `docs/`) created per plan.
- [x] Local dev tooling installed and verified working:
  - Node.js v22.20.0 (portable install under `C:\Users\<user>\cline-tools\node`,
    since the machine had no admin rights for the MSI installer).
  - PostgreSQL 16.13 (portable binaries, running on `localhost:5433`,
    database `cybertrace` created).
  - Python 3.14.7 venv at `backend/.venv`.
- [x] FastAPI app skeleton (`app/main.py`) with CORS and a `/api/health`
      endpoint that performs a **real** `SELECT 1` against the configured
      database and reports `db_connected: true/false` honestly (verified
      manually: returned `db_connected: true` against the running Postgres
      instance).
- [x] SQLAlchemy async models for all 8 tables in the approved schema
      (`users`, `cases`, `evidence_files`, `log_records`, `parse_errors`,
      `parsing_gaps`, `reports`, `audit_log`), with `timestamptz`-equivalent
      (`DateTime(timezone=True)`) columns throughout — verified against
      real PostgreSQL (`\dt` showed all 8 tables created correctly after
      fixing an initial timezone-naive/aware datetime bug).
- [x] Auth: `/api/auth/register`, `/api/auth/login`, `/api/auth/me` with
      bcrypt password hashing and JWT issuing/verification. Rate limiting
      (`slowapi`) applied to `/api/auth/login`.
  - Verified manually end-to-end against real Postgres: register → login →
    me returns the correct user; wrong password → 401; missing token → 401.
- [x] Backend test suite: **17/17 tests passing** (`pytest -v`), covering
      SHA-256 hashing utilities, password hashing, JWT roundtrip/tamper
      rejection, and the full auth API (register/login/me, duplicate email,
      short password, wrong password, unknown email, missing/invalid token)
      — run against an isolated in-memory SQLite DB per PROJECT_PLAN.md
      section 13.
- [x] Frontend scaffold: Vite + React 18 + TypeScript + Tailwind, built
      manually (the `npm create vite` interactive prompt could not be
      satisfied non-interactively in this environment, so the project files
      were created directly).
- [x] Design-system components implementing PROJECT_PLAN.md sections 1/1A:
      `Button`, `Badge`, `Card`, `Table` (with explicit loading/error/empty
      states), `Drawer`, `Logo`, `Sidebar`/`AppLayout` navigation shell.
- [x] Auth flow on the frontend: `AuthProvider`/`useAuth`, `Login` page,
      `ProtectedRoute` wrapper, token persisted in `localStorage`.
- [x] Dashboard page: intentionally small, shows live `/api/health` data
      (no fake stats), links into Timeline/Scenarios.
- [x] Remaining nav pages (Cases, Evidence, Timeline, Parse Errors,
      Scenarios, Reports) show an explicit "not implemented yet, backend
      endpoint pending" state rather than placeholder/fake data, per the
      anti-pattern checklist in PROJECT_PLAN.md section 1A.
- [x] Frontend test suite: **9/9 tests passing** (`vitest run`) covering
      Button (render, click, disabled), Badge (status/synthetic labels),
      Table (empty/loading/error/data states).
- [x] Frontend production build verified: `npm run build` succeeds
      (TypeScript strict-mode compile + Vite bundle, no errors).
- [x] `docs/TIMEZONE_POLICY.md` written per the plan's documentation
      requirement.
- [x] `.env.example`, `.gitignore`, `README.md` with real setup/run/test
      instructions.

### Known issues / environment notes from Phase 1
- Password hashing required pinning `bcrypt==4.0.1` (the latest bcrypt 5.x
  removed an attribute that `passlib` 1.7.4 depends on, causing a
  misleading "password too long" error). This should be revisited if
  `passlib` is ever upgraded.
- SQLAlchemy async requires `greenlet`, which is not pulled in by default
  on Python 3.14 — explicitly added to `pyproject.toml`.
- `npm audit` reports 15 vulnerabilities, all in **dev-only build tooling**
  (vite/vitest/tailwind/postcss transitive dependencies), none in the
  production runtime bundle. Fixing them requires breaking major-version
  upgrades (e.g. Tailwind v3→v4, Vitest major bump); deferred rather than
  applied blindly mid-scaffold. Will revisit before a production deploy.
- Alembic is installed but migrations have not been generated yet — Phase 1
  used `Base.metadata.create_all()` for speed. Real migrations will be
  added once the schema stabilizes further (Phase 3+).

## Phase 2 — Auth (folded into Phase 1)

Auth was implemented ahead of schedule as part of Phase 1 scaffolding
(register/login/me, JWT middleware, protected frontend routes) since it was
needed to demonstrate a working end-to-end slice. No further auth work is
planned as a separate phase unless requirements change.

## Phase 3 — Cases + Evidence upload + hashing — ✅ COMPLETE

- [x] Case CRUD endpoints (`/api/cases`): `GET /api/cases` (own + synthetic
      cases only), `POST /api/cases`, `GET /api/cases/{id}` (with live
      evidence/log-record/parse-error counts), `DELETE /api/cases/{id}`.
      Per-user authorization enforced: a private case is only visible to
      its creator (or an `admin` role); synthetic cases are shared
      read-only; other users get 403/404 as appropriate, never another
      user's data.
  - Files: `backend/app/schemas/case.py`, `backend/app/routers/cases.py`,
    wired into `backend/app/main.py`.
  - Tests: `backend/tests/integration/test_cases_api.py` — 8 new tests
    (auth required, create+list, validation, cross-user isolation,
    detail counts, 404, owner delete, non-owner delete forbidden).
  - **Regression found and fixed**: running the full suite (not just the
    new file) caused 2 failures (`KeyError: 'access_token'`) because the
    login rate limiter (`slowapi`, 10/min) is a process-wide in-memory
    store keyed by client IP, and all test requests share the same ASGI
    test-client IP — so accumulated logins across the whole suite started
    hitting 429s. Fixed by resetting `limiter` in the `client` fixture
    between tests (`backend/tests/conftest.py`). This only affects test
    isolation, not production behavior.
  - **Verified: full backend suite 25/25 passing** after the fix
    (`pytest -q` → `25 passed, 1 warning`).
- [x] Evidence upload endpoint with streaming SHA-256
  - `POST /api/cases/{case_id}/evidence`: streams to a temp file on disk
    with a size-limit check per chunk (no full-file memory buffering),
    hashes the exact bytes written (not the in-memory buffer), stores the
    final file at `{storage_root}/{case_id}/{sha256}{ext}`, and runs
    content-based format detection (`app/services/format_detection.py`)
    rather than trusting a client-declared format. Extension allow-list
    (`.log`, `.txt`, `.json`) and empty-file rejection enforced before any
    bytes are kept.
  - Files: `backend/app/routers/evidence.py`, `backend/app/schemas/evidence.py`,
    `backend/app/services/format_detection.py`, wired into `backend/app/main.py`.
- [x] Evidence list/download/verify-integrity endpoints
  - `GET /api/cases/{case_id}/evidence` (list, same per-case authorization
    as cases), `GET /api/evidence/{id}/download` (returns the original
    unmodified bytes via `FileResponse`), `GET /api/evidence/{id}/verify`
    (re-reads the stored file from disk and recomputes SHA-256 live on
    every call — never a cached flag — reporting both hashes and a clear
    mismatch/missing-file error when verification fails).
  - **Verified: full backend suite 34/34 passing** (`pytest -q` →
    `34 passed, 1 warning`), including
    `tests/integration/test_evidence_api.py` (9 tests: auth required,
    hash+format detection correctness, disallowed extension, empty file,
    cross-user upload forbidden, list, download returns exact original
    bytes, verify passes on an untouched file, and verify correctly
    reports a mismatch after directly corrupting the stored file on disk
    — a real tamper-detection test, not a hypothetical).
- [x] Cases and Evidence pages (replacing previous "Coming Soon" placeholders)
  - `frontend/src/pages/Cases.tsx`: create-case form (name + optional
    description, validated, real `POST /api/cases`), live case list via
    the shared `Table` component (loading/error/empty states), "Synthetic
    scenario" badge for shared demo cases, delete (owner-only, hidden for
    synthetic cases), and a link into the Evidence page per case.
  - `frontend/src/pages/Evidence.tsx`: case selector, file upload (real
    `multipart/form-data` POST via a new `api.postForm` client helper),
    and an evidence table with the exact columns required by
    PROJECT_PLAN.md section 1A.B — filename, detected format, size,
    uploaded-at (UTC, ISO), SHA-256 (truncated + "Copy full hash"),
    timezone assumption, and a verification-status badge
    (`Not yet verified` / `Verified` / `Hash mismatch`) driven by a real
    `GET /api/evidence/{id}/verify` call per row (not a cached flag) and a
    real `GET /api/evidence/{id}/download` (reads the `Content-Disposition`
    filename via a new `api.download` client helper; required adding
    `expose_headers=["Content-Disposition"]` to the backend CORS
    middleware in `backend/app/main.py`, since browsers hide all response
    headers except a small safelist under CORS by default).
  - New files: `frontend/src/pages/Cases.tsx`, `frontend/src/pages/Evidence.tsx`,
    `frontend/src/types/case.ts`, `frontend/src/types/evidence.ts`.
  - Changed files: `frontend/src/api/client.ts` (added `postForm` and
    `download` helpers), `frontend/src/App.tsx` (routes now render the
    real pages instead of `ComingSoon`), `backend/app/main.py` (CORS
    `expose_headers`).
  - **Verified**: `npm run build` succeeds (TypeScript strict-mode compile
    + Vite bundle, no errors); `npm run test` → **9/9 passing** (unchanged,
    no regressions — the existing Button/Badge/Table suites still cover
    the shared components these new pages reuse); backend suite re-run
    after the CORS change → **34/34 passing**.

## Phase 4 — Parsers (syslog, Apache, Windows JSON) — ✅ CORE COMPLETE

- [x] `syslog_auth` parser + unit tests (valid + malformed fixtures)
  - `backend/app/parsers/syslog_auth.py`: regex-matches
    `"Mon DD HH:MM:SS host process[pid]: message"`, classifies
    `auth_failure`/`auth_success`/`sudo_command`/`ssh_event` with
    source_ip/user extraction, applies the uploader's
    `timezone_assumption` + a reference year (no year/tz in the source
    line, per `docs/TIMEZONE_POLICY.md`). Malformed lines (no regex match,
    unparseable timestamp) become `ParseErrorRecord`, never raise/skip.
- [x] `apache_access` parser + unit tests
  - `backend/app/parsers/apache_access.py`: regex-matches the combined
    log format, uses the **embedded** `+ZZZZ` offset directly (uploader's
    assumption recorded but intentionally not applied, per policy),
    derives `event_type="http_request"` and severity from the HTTP status
    code (5xx→critical, 4xx→warning, else info).
- [x] `windows_evtx_json` parser + unit tests
  - `backend/app/parsers/windows_evtx_json.py`: accepts either a JSON
    array (`Get-WinEvent | ConvertTo-Json`) or JSON-Lines; uses the
    ISO-8601 offset in `TimeCreated` directly if present, else falls back
    to the uploader's timezone assumption; severity derived from
    `LevelDisplayName`/`Level`. A single malformed line in JSON-Lines mode
    is isolated as one `ParseErrorRecord` without sinking the other lines;
    an invalid top-level JSON array is reported as one line-1 error.
  - New dependency: `tzdata` (added to `backend/pyproject.toml`) — required
    for Python's `zoneinfo` to resolve IANA timezone names on Windows,
    which has no system tz database. Installed into `backend/.venv` and
    verified.
- [x] Ingestion service wiring parse errors/gaps
  - `backend/app/services/ingestion.py`: dispatches on `detected_format`
    via a `PARSERS` registry (`backend/app/parsers/__init__.py`), writes
    one `LogRecord` row per successfully parsed line (preserving
    `line_number` and the verbatim `raw_line`) or one `ParseError` row per
    failed line, and flags a `ParsingGap` row whenever two consecutive
    successfully-parsed timestamps jump by more than 3600s.
  - Wired into `POST /api/cases/{case_id}/evidence`
    (`backend/app/routers/evidence.py`): after the evidence file is
    hashed and stored unmodified, its full text is read **read-only** and
    passed to the ingestion service; the endpoint now returns real
    `records_parsed`/`records_failed`/`gaps_detected` counts instead of
    hardcoded zeros. The original stored file is never reopened in write
    mode after upload — evidence preservation is unaffected.
  - Updated `tests/integration/test_evidence_api.py::test_upload_evidence_computes_sha256_and_detects_format`
    to assert the now-real parsed/failed counts (previously asserted the
    honest placeholder zeros, which are no longer accurate).
- [x] Ingestion summary surfaced in the upload UI
  - `frontend/src/pages/Evidence.tsx`: after a successful upload, the
    Upload card now shows `records_parsed`/`records_failed`/`gaps_detected`
    from the real `EvidenceUploadResponse` (not a toast or invented
    stat). Loading (`Uploading and parsing…`), error (`role="alert"` with
    the backend's message), and success states are all explicit; the
    summary is cleared when a new upload starts or a prior one errors.
  - New test `frontend/src/pages/Evidence.test.tsx` (2 tests, mocking
    `api.get`/`api.postForm`): asserts the parsed/failed/gaps counts
    render after a successful upload, and that a failed upload shows the
    error alert with no stale summary.
- **Verified**: new targeted suite `tests/unit/test_parsers.py` (14 tests)
  + `tests/unit/test_ingestion.py` (3 tests) → **17/17 passing**.

## Phase 5 — Timeline + search — ✅ CORE COMPLETE

- [x] `/api/cases/{id}/timeline` with filters/pagination
  - `backend/app/routers/timeline.py` (new) + `backend/app/schemas/timeline.py`
    (new): `GET /api/cases/{case_id}/timeline` supports `q` (free-text over
    `message`/`raw_line`), `start_time`/`end_time` (ISO datetime range on
    `event_time_utc`), `event_type`, `severity`, `source` (matches
    `source_ip` or `user_or_actor`), `sort`/`order` (only `event_time_utc`
    is an allowed sort field, enforced server-side with a 400 on anything
    else), and `limit`/`offset` pagination. Reuses
    `cases.get_authorized_case` for the same per-user/admin/synthetic
    access rules as every other case-scoped endpoint. Each returned record
    is denormalized with its source evidence file's name + SHA-256 and a
    `near_parse_gap` flag computed by joining against `parsing_gaps` for
    that evidence file — all real joins, no client-side guessing.
- [x] Timeline page (7-column table per PROJECT_PLAN.md section 1A)
  - `frontend/src/pages/Timeline.tsx` (new) + `frontend/src/types/timeline.ts`
    (new): case selector, filter controls (search, severity, event type,
    source, start/end time, sort-order toggle) all wired to real
    `GET /api/cases/{id}/timeline` query parameters, a `Table` with
    Timestamp(UTC)+original timezone, Source, Event type, Severity badge,
    and Parsing status badge (`Parsed` / `Near parse gap`) columns, and a
    row-click `Drawer` showing the full `raw_line`, source evidence
    filename+hash, and line number. Route wired in `App.tsx` (replaces the
    prior `ComingSoon` placeholder).
- [x] `frontend/src/pages/Timeline.test.tsx` (new, 3 tests): renders real
  timeline records with event type/severity/source, opens the detail
  drawer on row click and shows `raw_line` + evidence filename + line
  number, and shows the "select a case" empty state when no case is
  selected.
- **Verified**: new backend suite `tests/integration/test_timeline_api.py`
  (11 tests covering auth-required, default ascending order, descending
  sort, severity/event_type/source filters, free-text search, date-range
  filter, pagination, cross-user 403, and rejecting an unsupported sort
  field) → **11/11 passing**.

## Phase 6 — Parse Errors / Gaps UI — ✅ COMPLETE

- [x] `GET /api/cases/{id}/parse-issues`: combined `parse_errors` +
  `parsing_gaps` for a case, each denormalized with the source evidence
  filename, reusing `cases.get_authorized_case` for the same per-user
  access control as every other case-scoped endpoint.
  (`backend/app/routers/parse_issues.py`, `backend/app/schemas/parse_issues.py`)
- [x] `frontend/src/pages/ParseErrors.tsx` (new): case selector, a
  "Malformed records" table (source evidence, line number, raw line,
  reason, parser) and a "Detected parsing gaps" table (source evidence,
  line range, description), plus a compact real count strip. Route wired
  in `App.tsx`, replacing the `ComingSoon` placeholder.
- **Verified**: `tests/integration/test_parse_issues_api.py` (4 tests:
  auth required, errors+gaps returned with correct line numbers/reasons
  for a mixed-content fixture, empty case returns empty arrays, cross-user
  403) → **4/4 passing**. `frontend/src/pages/ParseErrors.test.tsx` (3
  tests) → **3/3 passing**.

## Phase 7 — Synthetic scenarios — ✅ COMPLETE

- [x] 3 scenario generators + bundled sample logs, committed under
  `backend/sample_logs/`: `ssh_bruteforce.log` (syslog, repeated failed
  logins + one success + a sudo command, with 2 corrupted lines),
  `sql_injection_probe.log` (Apache combined log, SQLi payloads mixed with
  normal traffic, with 2 malformed lines), `phishing_lateral_movement.json`
  (Windows Event Log JSON array: suspicious remote logon → process
  creation → privilege escalation, with a deliberate out-of-order
  clock-skew-style timestamp).
- [x] `GET /api/scenarios` + `POST /api/scenarios/{key}/load`
  (`backend/app/routers/scenarios.py`, `backend/app/services/scenarios.py`):
  loading a scenario creates a brand-new `is_synthetic=True` case and runs
  the sample log through the **exact same** hash/store/detect/ingest
  pipeline used for a real upload (`sha256_of_bytes`, `detect_format`,
  `ingest_evidence_file`) — not a separate, less-trustworthy seed path.
- [x] `frontend/src/pages/Scenarios.tsx` (new): lists all 3 scenarios with
  descriptions, a persistent "Synthetic scenario" `Badge`, a "Load
  scenario" button per card, and shows the real post-load
  parsed/failed/gaps summary with a link into that case's Timeline. Route
  wired in `App.tsx`.
- **Verified**: `tests/integration/test_scenarios_api.py` (7 tests: list
  returns all 3 keys, load requires auth, unknown scenario → 404, each of
  the 3 scenarios loads with the expected non-zero `records_parsed` and
  (for 2 of 3) non-zero `records_failed`, synthetic case visible to other
  users) → **7/7 passing**. `frontend/src/pages/Scenarios.test.tsx` (3
  tests) → **3/3 passing**.

## Phase 8 — Reports export — ✅ COMPLETE

- [x] JSON / CSV / PDF export endpoints
  (`backend/app/routers/reports.py`, `backend/app/services/report_export.py`):
  `POST /api/cases/{id}/reports?format={json|csv|pdf}` generates the file
  from the same real DB rows used elsewhere (case, evidence files,
  log_records, parse_errors, parsing_gaps), writes it once to
  `REPORTS_STORAGE_DIR/{case_id}/{report_id}.{ext}`, and records a `Report`
  row; `GET /api/cases/{id}/reports` lists past reports;
  `GET /api/reports/{id}/download` streams the stored file. JSON is the
  full machine-readable export; CSV is a zip of two separate
  consistent-column files (`timeline_records.csv`, `parse_errors.csv`);
  PDF (via `reportlab`, pure-Python — no system libs needed on Windows,
  unlike WeasyPrint) has a cover/summary section, the timeline table, and
  an explicit "Unparsed / anomalous records" section so gaps are visible
  in the delivered report, not just the UI.
  - New dependency: `reportlab>=4.0.0` (added to `backend/pyproject.toml`).
- [x] `frontend/src/pages/Reports.tsx` (new): case selector, "Generate
  JSON/CSV/PDF" buttons wired to the real endpoint, a table of past
  reports with format + generated-at (UTC) + a real download action. Route
  wired in `App.tsx`.
- **Verified**: `tests/integration/test_reports_api.py` (6 tests: auth
  required, JSON export round-trips real case data incl. evidence
  hash/parse errors, CSV export unzips to the two expected files with
  real content, PDF export returns valid `%PDF` bytes, listing reports,
  cross-user 403 on both generate and download) → **6/6 passing**.
  `frontend/src/pages/Reports.test.tsx` (3 tests) → **3/3 passing**.

## Manual-vs-automated triage-time comparison — ✅ COMPLETE

- [x] `backend/app/services/ingestion.py` now measures real wall-clock
  `automated_seconds` for the parse+ingest stage and computes a clearly
  labeled `manual_estimate_seconds` assumption (`15s` per line, a named
  constant, applied to the real parsed+failed line count) — following the
  same "assumption vs. measured value, always labeled" principle already
  used for timezones (`docs/TIMEZONE_POLICY.md`). Both fields flow through
  `EvidenceUploadResponse` and are shown in the Evidence page upload
  summary as "Automated parsing took Xs (measured)" vs. "Manual triage ...
  estimated at Y min (assumption: ~15s/line ..., not measured)" — the
  estimate is never presented as a fact.
- **Verified**: `tests/unit/test_ingestion.py` (+1 new test: automated
  time is a real non-negative measurement, manual estimate is
  deterministically `line_count * 15`) plus the unknown-format test
  updated to check `manual_estimate_seconds == 0.0`.
  `tests/integration/test_evidence_api.py` updated to assert both new
  response fields.

## Phase 9 — Security hardening pass — ✅ COMPLETE (pip-audit deferred)

- [x] Rate limiting on login
- [x] Bcrypt password hashing
- [x] JWT auth on protected endpoints
- [x] CORS restricted to configured frontend origin
- [x] Audit log wiring: `backend/app/services/audit.py` (append-only
  writer) is now called from `login`/failed-login
  (`app/routers/auth.py`), `evidence_upload` (`app/routers/evidence.py`),
  `report_export` (`app/routers/reports.py`), and `case_delete`
  (`app/routers/cases.py`). A new admin-only `GET /api/audit-log`
  (`backend/app/routers/audit.py`) lets an admin user review the trail;
  non-admins get 403.
  - **Verified**: `tests/integration/test_audit_log_api.py` (5 tests: auth
    required, non-admin 403, successful login recorded, failed login
    recorded, evidence-upload + case-delete recorded) → **5/5 passing**.
- [x] Upload validation (extension allow-list, size limit, streamed
  hashing) — already implemented in Phase 3 and re-verified still passing.
- [x] `.env.example` added (was missing despite `.gitignore` already
  excluding `.env`) documenting `DATABASE_URL`, `JWT_SECRET_KEY`,
  `EVIDENCE_STORAGE_DIR`, `REPORTS_STORAGE_DIR` with a warning that the
  JWT secret must be a long random value outside local dev.
- [ ] Dependency vulnerability review: backend scan remains deferred
  because `pip-audit` is not installed in the existing backend venv.
  Frontend `npm audit --json` is recorded under Phase 10 below.
- **Security review summary (manual code read, this session)**:
  - **Auth**: bcrypt hashing, JWT HS256 with expiry, `/api/auth/login`
    rate-limited via `slowapi`. Login failures return a generic "Invalid
    email or password" (no user-enumeration via differing error text).
  - **Case-level access control**: every case-scoped router
    (`cases`, `evidence`, `timeline`, `parse_issues`, `reports`) funnels
    through the single `cases.get_authorized_case`/`can_modify` pair, so
    the authorization rule (owner, admin, or read-only for
    `is_synthetic` cases) is defined once and reused, not reimplemented
    per-router.
  - **Uploads**: extension allow-list enforced before any bytes are kept;
    size limit enforced per-chunk during streaming (not after full read);
    empty files rejected; SHA-256 computed from bytes actually written to
    disk, not the in-memory buffer.
  - **Evidence hash verification**: `GET /api/evidence/{id}/verify`
    re-reads the file and recomputes SHA-256 on every call (no cached
    flag); a corrupted-on-disk file is a real, tested failure path.
  - **Preservation of original files**: evidence files are written once
    to a content-addressed path and never reopened in write mode after
    upload; the ingestion step that reads the file for parsing opens it
    strictly read-only (`open(..., "r")`). Report files are similarly
    written once and only read back for download.

## Phase 10 — Testing and polish — VERIFIED

- **Backend**: From `D:\CyberTrace\backend`, ran
  `.venv\Scripts\python.exe -m pytest -q` → **89 passed, 1 warning**
  in 39.75s. The warning is SlowAPI's deprecated use of
  `asyncio.iscoroutinefunction`.
- **Frontend**: From `D:\CyberTrace\frontend`, ran
  `npm.cmd run test` → **25 passed across 9 files**. React Router
  continues to emit v7 future-flag warnings.
- **Production build**: `npm.cmd run build` passed TypeScript and Vite;
  output includes `frontend/dist/index.html` and hashed static assets.
- **Browser checks**: Account creation and sign-in succeeded; the
  dashboard showed live API/database health and live case counts; the
  responsive mobile navigation rendered at 390px without horizontal
  page overflow. The full case/evidence/hash/scenario/timeline/parse
  issue/report workflow checks are recorded above from the 2026-10-14
  verification.
- **Lint**: `npm.cmd run lint` is currently blocked by the existing
  missing ESLint 9 flat configuration (`eslint.config.js`); the project
  has no TypeScript ESLint parser/configuration. No dependencies were
  installed solely to make lint run. Ruff passed for the modified
  backend files.

## Hosting and interface polish

- Added a responsive dark incident-response workspace shell, compact
  mobile navigation, refined cards/tables/status badges, a branded
  sign-in/account-creation experience, and a dashboard with actual API
  health and case counts (no invented metrics).
- Added frontend registration using the existing `/api/auth/register`
  endpoint, followed by sign-in. Covered success/error behavior with two
  new Vitest tests and confirmed account creation in the local browser.
- Added `render.yaml` for a Render static frontend, FastAPI service,
  PostgreSQL 16 database, and persistent disk for evidence and reports.
  Render's standard `postgresql://` database URL is adapted to the
  existing asyncpg driver, with four unit-test cases covering both
  PostgreSQL URL schemes, already-async PostgreSQL, and SQLite.
- Updated `README.md` with the static build details and Render setup.
  `render.yaml` parsed and its database, persistent disk, and SPA fallback
  were checked locally. The site has **not** been deployed to a public
  Render account; that requires connecting this project to GitHub and
  accepting Render's paid API/database/disk resources.
- **Dependency audit limitations**: The last `npm.cmd audit --json`
  reported 15 frontend findings (2 critical, 6 high, 7 moderate), with
  2 moderate in the production dependency tree. The suggested React
  Router remediation requires a major upgrade and was not applied.
  `pip-audit` remains unavailable in the existing backend venv; no
  package was installed for this check.
- No schema changes were made. Evidence upload remains content-addressed
  and SHA-256 verification still checks the stored original bytes.

## Reproduction commands

- Backend tests: from `D:\CyberTrace\backend`, run
  `.venv\Scripts\python.exe -m pytest -q`.
- Frontend tests/build: from `D:\CyberTrace\frontend`, run
  `npm.cmd run test` and `npm.cmd run build`.
- Frontend dependency audits: from `D:\CyberTrace\frontend`, run
  `npm.cmd audit --json` and `npm.cmd audit --omit=dev --json`.
- Backend health: `curl.exe http://127.0.0.1:8000/api/health`.
