import pytest
from sqlalchemy.engine import URL

from app.db import normalize_async_database_url


@pytest.mark.parametrize("scheme", ["postgres", "postgresql"])
def test_normalize_async_database_url_adds_postgresql_driver(scheme: str) -> None:
    url = normalize_async_database_url(
        f"{scheme}://cybertrace:p%40ss@db.example.com:5432/cybertrace"
    )

    assert isinstance(url, URL)
    assert url.drivername == "postgresql+asyncpg"
    assert url.username == "cybertrace"
    assert url.password == "p@ss"
    assert url.host == "db.example.com"
    assert url.port == 5432
    assert url.database == "cybertrace"


def test_normalize_async_database_url_preserves_async_postgresql_url() -> None:
    value = "postgresql+asyncpg://cybertrace@db.example.com/cybertrace"

    assert normalize_async_database_url(value) == value


def test_normalize_async_database_url_preserves_sqlite_url() -> None:
    value = "sqlite+aiosqlite:///./cybertrace.db"

    assert normalize_async_database_url(value) == value
