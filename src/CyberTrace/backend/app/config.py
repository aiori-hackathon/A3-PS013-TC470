"""Application settings, loaded from environment variables / .env file.

For Phase 1 scaffolding, the default DATABASE_URL points at a local SQLite
file so the backend runs without requiring PostgreSQL to be installed first.
Set DATABASE_URL to a postgresql+asyncpg:// URL (see .env.example) to use
PostgreSQL instead -- no code changes are required, only the connection
string, because all data access goes through SQLAlchemy's async engine.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "CyberTrace"
    environment: str = "development"

    # Default: local SQLite file for easy local development without Postgres.
    # Production / integration tests should set DATABASE_URL explicitly to
    # a PostgreSQL connection string, e.g.:
    #   postgresql+asyncpg://cybertrace:cybertrace@localhost:5432/cybertrace
    database_url: str = "sqlite+aiosqlite:///./cybertrace.db"

    jwt_secret_key: str = "dev-only-insecure-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60

    evidence_storage_dir: str = "./storage/evidence"
    max_upload_size_bytes: int = 200 * 1024 * 1024  # 200 MB
    reports_storage_dir: str = "./storage/reports"

    cors_allowed_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    login_rate_limit: str = "10/minute"


@lru_cache
def get_settings() -> Settings:
    return Settings()
