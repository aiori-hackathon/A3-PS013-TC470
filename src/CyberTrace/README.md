# CyberTrace

A small-team incident-timeline and evidence-ingestion tool. See
`PROJECT_PLAN.md` for the full architecture, schema, and phased plan.

From the repository root, enter `src/CyberTrace` before running the local
development commands below.

## Local development setup

### Prerequisites
- Python 3.11+ (tested with 3.14)
- Node.js 18+ (tested with 22.20.0)
- PostgreSQL 14+ (tested with 16.13)

### Backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

Create `backend/.env` (see `.env.example` at the repo root):

```
DATABASE_URL=postgresql+asyncpg://<user>@<host>:<port>/cybertrace
JWT_SECRET_KEY=<a long random value>
EVIDENCE_STORAGE_DIR=./storage/evidence
```

Create the database tables (dev convenience; Alembic migrations will be
added as the schema evolves):

```powershell
.venv\Scripts\python.exe -c "import asyncio; from app.db import init_models; import app.models; asyncio.run(init_models())"
```

Run the API:

```powershell
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

Run the backend test suite (uses an isolated in-memory SQLite DB, no
PostgreSQL required):

```powershell
.venv\Scripts\python.exe -m pytest -v
```

### Frontend

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

The dev server runs on `http://localhost:5173` and expects the API at
`http://localhost:8000` by default (see `frontend/.env`).

Run frontend tests:

```powershell
npm.cmd run test
```

Build for production:

```powershell
npm.cmd run build
```

The build creates a static website in `frontend/dist` (`index.html` plus
hashed assets). It is not a single self-contained HTML file: the JavaScript
application calls the CyberTrace API, so hosting only `index.html` will not
provide login, evidence storage, scenarios, or reports.

## Host on Render

The repository-root [`render.yaml`](../../render.yaml) Blueprint describes the complete
deployment:

- `cybertrace-web`: static React/Vite site, built from `frontend/dist`.
- `cybertrace-api`: FastAPI service.
- `cybertrace-db`: PostgreSQL 16.
- A persistent disk mounted at `/var/data` for original evidence and
  generated reports. Evidence remains content-addressed and its original
  bytes are still verified by the existing SHA-256 endpoint.

### Deploy

1. Push this project to a GitHub repository.
2. In Render, choose **New → Blueprint**, connect the repository, and
   review the resources and costs before applying `render.yaml`. The API
   plan and database are paid plans; the persistent disk is intentional so
   uploaded evidence is not lost when the API restarts. Render pricing and
   availability can change.
3. The Blueprint creates a random `JWT_SECRET_KEY`, initializes the
   existing SQLAlchemy tables before deployment, and configures storage,
   API URL, and CORS for the default service domains.
4. Open the static-site URL, create an account, and sign in. If you rename
   either service or attach a custom domain, update `VITE_API_BASE_URL` on
   `cybertrace-web` and `CORS_ALLOWED_ORIGINS` on `cybertrace-api` to the
   exact HTTPS origins, then redeploy.

The API's `DATABASE_URL` accepts Render's standard `postgresql://` URL and
uses the existing async PostgreSQL driver. Do not use SQLite or ephemeral
web-service storage for a hosted deployment that needs durable evidence.

## Project status

See `PROGRESS.md` for the current implementation checklist.
