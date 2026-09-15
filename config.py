import os
import secrets
from typing import List

from pydantic_settings import BaseSettings


def _secret_key() -> str:
    """Return the signing key for JWTs.

    There is deliberately no committed fallback value. If SECRET_KEY is not set,
    a random key is generated for this process only, which means tokens stop
    working when the server restarts. That is inconvenient on purpose: it makes
    a missing key obvious in development instead of shipping a key that is
    published in the repository and therefore lets anyone mint valid tokens.
    """
    return os.getenv("SECRET_KEY") or secrets.token_urlsafe(32)


class Settings(BaseSettings):
    PROJECT_NAME: str = "SIP Friction Analyzer"
    VERSION: str = "1.0.0"
    API_V1_STR: str = ""

    # Database
    # PostgreSQL is the target database. Override with DATABASE_URL.
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://sip_app:@localhost:5432/sip",
    )

    # Security
    SECRET_KEY: str = _secret_key()
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # CORS
    # Explicit origins rather than "*": browsers reject a wildcard origin when
    # credentials are allowed, so "*" here would silently break authenticated
    # requests from the browser.
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
    ]

    # Optional seed account.
    # No default password: if DEFAULT_ADMIN_PASSWORD is unset, no account is
    # created at all. Committing a known password would ship an open door.
    DEFAULT_ADMIN_USER: str = os.getenv("DEFAULT_ADMIN_USER", "admin")
    DEFAULT_ADMIN_PASSWORD: str = os.getenv("DEFAULT_ADMIN_PASSWORD", "")

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"


settings = Settings()
