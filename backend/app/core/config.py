"""
Application Configuration
Centralized configuration management using Pydantic Settings
"""
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # App Info
    APP_NAME: str = "Pregnancy Safety Radar API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str = "sqlite:///./pregnancy_safety.db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # AI APIs
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None

    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Monitoring
    SENTRY_DSN: Optional[str] = None

    # Google Cloud (OCR)
    GOOGLE_CLOUD_PROJECT_ID: Optional[str] = None
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    Cached settings instance
    Returns the same Settings object on subsequent calls
    """
    return Settings()


# Global settings instance
settings = get_settings()
