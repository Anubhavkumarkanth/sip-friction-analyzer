import os
import secrets
from typing import List

from pydantic_settings import BaseSettings


def _secret_key() -> str:
    """JWT signing key.

    No committed fallback - a published key would let anyone mint valid tokens.
    If SECRET_KEY is unset we generate a random one per process, so tokens break
    on restart, which makes the missing setting obvious.
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
