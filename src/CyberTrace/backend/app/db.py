"""Async SQLAlchemy engine/session setup, plus the declarative Base used by
all models.
"""
from collections.abc import AsyncGenerator

from sqlalchemy.engine import URL, make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()


def normalize_async_database_url(database_url: str) -> URL | str:
    """Adapt standard PostgreSQL URLs (such as Render's) to the async driver."""
    url = make_url(database_url)
    if url.drivername in {"postgres", "postgresql"}:
        return url.set(drivername="postgresql+asyncpg")
    return database_url


# echo=False by default; flip via code if deep SQL debugging is needed.
engine = create_async_engine(
    normalize_async_database_url(settings.database_url),
    echo=False,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a request-scoped async DB session."""
    async with AsyncSessionLocal() as session:
        yield session


async def init_models() -> None:
    """Create tables directly from models.

    Used for local/dev/test convenience (SQLite) and the test suite. In
    staging/production, Alembic migrations (backend/migrations) are the
    source of truth for schema changes.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
