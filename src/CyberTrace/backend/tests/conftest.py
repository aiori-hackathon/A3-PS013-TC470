"""Shared pytest fixtures.

Tests use an isolated in-memory SQLite database (not the dev PostgreSQL
instance) so the suite is fast, hermetic, and does not depend on a running
Postgres server. The same SQLAlchemy models/async session machinery is used
either way -- only the connection string differs, per PROJECT_PLAN.md's
"no code changes required" design for swapping databases.
"""
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

import app.models  # noqa: F401 ensures all models are registered on Base
from app.db import Base, get_db
from app.main import app
from app.rate_limit import limiter
from app.routers import evidence as evidence_router
from app.routers import reports as reports_router


@pytest.fixture(autouse=True)
def _isolated_evidence_storage(tmp_path, monkeypatch):
    """Redirects evidence uploads to a per-test temp directory so the test
    suite never writes into the real dev `storage/evidence` folder."""
    monkeypatch.setattr(evidence_router.settings, "evidence_storage_dir", str(tmp_path))
    monkeypatch.setattr(
        reports_router.settings, "reports_storage_dir", str(tmp_path / "reports")
    )


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)

    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session):
    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    # The login rate limiter is a process-wide in-memory store keyed by
    # client IP. Since all test requests share the same ASGI transport
    # "IP", the limiter's state must be reset between tests, otherwise
    # tests run later in the full suite see 429s from earlier tests'
    # login calls. This does not affect production behavior.
    limiter.reset()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
