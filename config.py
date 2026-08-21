import os
from typing import List

try:
    from pydantic_settings import BaseSettings

    class Settings(BaseSettings):
        PROJECT_NAME: str = "SIP Friction Analyzer"
        VERSION: str = "1.0.0"
        API_V1_STR: str = ""
        
        # Database
        DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./sip.db")
        
        # Security
        SECRET_KEY: str = os.getenv("SECRET_KEY", "development-secret-key-change-in-production-f89a2b")
        ALGORITHM: str = "HS256"
        ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
        
        # CORS
        CORS_ORIGINS: List[str] = ["*"]
        
        # Seed user configuration
        DEFAULT_ADMIN_USER: str = os.getenv("DEFAULT_ADMIN_USER", "admin")
        DEFAULT_ADMIN_PASSWORD: str = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")

        class Config:
            case_sensitive = True
            env_file = ".env"
            extra = "ignore"

    settings = Settings()

except ImportError:
    # Standard fallback when pydantic_settings is not installed in local environment
    class Settings:  # type: ignore
        PROJECT_NAME: str = "SIP Friction Analyzer"
        VERSION: str = "1.0.0"
        API_V1_STR: str = ""
        DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./sip.db")
        SECRET_KEY: str = os.getenv("SECRET_KEY", "development-secret-key-change-in-production-f89a2b")
        ALGORITHM: str = "HS256"
        ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
        CORS_ORIGINS: List[str] = ["*"]
        DEFAULT_ADMIN_USER: str = os.getenv("DEFAULT_ADMIN_USER", "admin")
        DEFAULT_ADMIN_PASSWORD: str = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")

    settings = Settings()
