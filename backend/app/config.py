"""
Application configuration.

DATABASE_URL defaults to a local SQLite file so the prototype runs with zero
external dependencies. Set DATABASE_URL to a PostgreSQL DSN (e.g.
postgresql+psycopg2://user:pass@localhost:5432/enterprise_ai) to use the
docker-compose Postgres instance described in the README -- no code changes
are required, SQLAlchemy handles both.
"""
import os
from functools import lru_cache


class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./enterprise_ai.db")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8

    OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY") or None
    ANTHROPIC_API_KEY: str | None = os.getenv("ANTHROPIC_API_KEY") or None
    GOOGLE_API_KEY: str | None = os.getenv("GOOGLE_API_KEY") or None
    GITHUB_TOKEN: str | None = os.getenv("GITHUB_TOKEN") or None

    # Publicly documented list pricing used ONLY when a connector legitimately
    # reports token usage. These are configuration, not observed values.
    PROVIDER_PRICING_PER_MILLION_TOKENS: dict = {
        "openai": {"input": 2.50, "output": 10.00},
        "anthropic": {"input": 3.00, "output": 15.00},
        "google": {"input": 1.25, "output": 5.00},
    }


@lru_cache
def get_settings() -> Settings:
    return Settings()
