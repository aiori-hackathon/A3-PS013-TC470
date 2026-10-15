"""CyberTrace FastAPI application entrypoint.

Phase 1 scaffolding: app factory, CORS, and a health check endpoint that
verifies the database connection is actually reachable (not just a static
"ok" response), since an honest health check is part of making failures
visible rather than hidden.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text

from app.config import get_settings
from app.db import engine
from app.rate_limit import limiter
from app.routers import audit, auth, cases, evidence, parse_issues, reports, scenarios, timeline

settings = get_settings()

app = FastAPI(title=settings.app_name, version="0.1.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    # Without this, the browser's fetch() API cannot read the
    # Content-Disposition header on evidence downloads (CORS hides all
    # response headers except a small safelist by default), so the
    # frontend could not recover the original filename for the download.
    expose_headers=["Content-Disposition"],
)

app.include_router(auth.router)
app.include_router(cases.router)
app.include_router(evidence.router)
app.include_router(timeline.router)
app.include_router(parse_issues.router)
app.include_router(reports.router)
app.include_router(scenarios.router)
app.include_router(audit.router)


@app.get("/api/health")
async def health_check() -> dict:
    """Reports whether the API process is up AND whether it can reach the
    configured database. Returns db_connected=False (not a 500) when the
    database is unreachable, so the frontend can show a clear error state
    instead of a generic network failure.
    """
    db_connected = False
    db_error: str | None = None
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_connected = True
    except Exception as exc:  # noqa: BLE001 - we want to report any DB error, not hide it
        db_error = str(exc)

    return {
        "status": "ok",
        "app_name": settings.app_name,
        "environment": settings.environment,
        "db_connected": db_connected,
        "db_error": db_error,
    }
