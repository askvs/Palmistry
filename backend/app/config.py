from pathlib import Path
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parent.parent.parent / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "Palmistry & Tarot Intelligence Platform"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    APP_VERSION: str = "0.1.0"

    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 14

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/google/callback"
    FRONTEND_URL: str = "http://localhost:3000"
    REFRESH_COOKIE_SECURE: bool = False

    AUTH_RATE_LIMIT_PER_MINUTE: int = 10

    # Invite code for admin self-signup; empty disables it.
    ADMIN_SIGNUP_CODE: str = "ADMIN"

    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/palmistry"
    DATABASE_TEST_URL: str = (
        "postgresql+psycopg://postgres:postgres@localhost:5432/palmistry_test"
    )

    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "qwen/qwen3.8-27b"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    LLM_PROVIDER: str = ""  # "openai", "groq", or "" for auto-detect

    MAX_UPLOAD_SIZE_MB: int = 10
    RATE_LIMIT_PER_MINUTE: int = 60
    DAILY_GUIDANCE_HOUR: int = 8

    UPLOAD_DIR: str = "uploads"
    AVATAR_MAX_SIZE_MB: int = 5

    # Live consultation & booking settings.
    BOOKING_MIN_LEAD_MINUTES: int = 60
    BOOKING_MAX_ADVANCE_DAYS: int = 60
    BOOKING_CANCEL_WINDOW_HOURS: int = 24
    BOOKING_REMINDER_LEAD_MINUTES: int = 1440
    BOOKING_SHORT_REMINDER_LEAD_MINUTES: int = 60
    BOOKING_SLOT_HORIZON_DAYS: int = 21
    BOOKING_ROLLOUT_HOUR: int = 1

    # Email (SMTP) settings.
    EMAIL_SMTP_HOST: str = ""
    EMAIL_SMTP_PORT: int = 587
    EMAIL_SMTP_USER: str = ""
    EMAIL_SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = "noreply@palmistry.local"
    EMAIL_FROM_NAME: str = "MysticLens Divination"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

if settings.ENVIRONMENT == "production" and settings.DEBUG:
    raise RuntimeError("DEBUG must be false in production (set DEBUG=false)")
