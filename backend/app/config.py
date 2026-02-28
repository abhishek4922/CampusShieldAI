"""
CampusShield AI — Application Configuration

Uses Pydantic Settings for type-safe, environment-variable-driven config.
All secrets come from environment variables; no hardcoded credentials.
"""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyUrl, Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── App ─────────────────────────────────────────────────
    APP_ENV: str = "development"
    APP_DEBUG: bool = False
    APP_SECRET_KEY: str
    ALLOWED_HOSTS: List[str] = ["*"]
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]

    # ── Database ────────────────────────────────────────────
    DATABASE_URL: str
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "campusshield"
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str

    # ── Redis ───────────────────────────────────────────────
    REDIS_URL: str
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""

    # ── JWT ─────────────────────────────────────────────────
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── OAuth ───────────────────────────────────────────────
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    MICROSOFT_CLIENT_ID: str = ""
    MICROSOFT_CLIENT_SECRET: str = ""
    OAUTH_REDIRECT_URI: str = "http://localhost:8000/v1/auth/oauth/callback"

    # ── ML Microservice ─────────────────────────────────────
    ML_SERVICE_URL: str = "http://ml_service:8001"
    ML_SERVICE_API_KEY: str = ""

    # ── Rate Limiting ───────────────────────────────────────
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_BURST: int = 20

    # ── Differential Privacy ────────────────────────────────
    DP_EPSILON: float = Field(default=1.0, description="Privacy budget ε per snapshot")
    DP_SENSITIVITY: float = Field(default=1.0, description="L1 query sensitivity")

    # ── Monitoring ──────────────────────────────────────────
    PROMETHEUS_ENABLED: bool = True


# Global singleton — import from app.config import settings
settings = Settings()
