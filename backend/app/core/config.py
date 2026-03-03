"""
Application settings loaded from environment variables.
Uses pydantic-settings for type-safe configuration.
"""

from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── General ──────────────────────────────────────────────
    APP_NAME: str = "VoiceAgentPlatform"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "change-me-to-a-random-64-char-string"
    ALLOWED_HOSTS: str = "localhost,127.0.0.1"

    # ── Backend ──────────────────────────────────────────────
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    BACKEND_WORKERS: int = 4
    LOG_LEVEL: str = "info"

    # ── Database ─────────────────────────────────────────────
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "voiceagent"
    POSTGRES_USER: str = "voiceagent"
    POSTGRES_PASSWORD: str = "changeme_pg_password"

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def DATABASE_URL_SYNC(self) -> str:
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # ── Redis ────────────────────────────────────────────────
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""

    @property
    def REDIS_URL(self) -> str:
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    @property
    def CELERY_BROKER_URL(self) -> str:
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/1"

    @property
    def CELERY_RESULT_BACKEND(self) -> str:
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/2"

    # ── Auth / JWT ───────────────────────────────────────────
    JWT_SECRET_KEY: str = "change-me-jwt-secret-64-chars"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Twilio ───────────────────────────────────────────────
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""
    TWILIO_WEBHOOK_BASE_URL: str = "https://your-domain.com"

    # ── OpenAI ───────────────────────────────────────────────
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4"
    OPENAI_WHISPER_MODEL: str = "whisper-1"

    # ── ElevenLabs (TTS) ────────────────────────────────────
    ELEVENLABS_API_KEY: str = ""
    ELEVENLABS_VOICE_ID: str = ""

    # ── Azure TTS ────────────────────────────────────────────
    AZURE_SPEECH_KEY: str = ""
    AZURE_SPEECH_REGION: str = ""

    # ── Custom AI Server (VPS) ──────────────────────────────
    CUSTOM_AI_SERVER_ENDPOINT: str = ""
    CUSTOM_AI_SERVER_API_KEY: str = ""
    CUSTOM_AI_SERVER_TIMEOUT: int = 120
    CUSTOM_AI_SERVER_MAX_RETRIES: int = 2
    CUSTOM_AI_SERVER_HEALTH_INTERVAL: int = 30

    # ── Google Sheets ────────────────────────────────────────
    GOOGLE_SERVICE_ACCOUNT_FILE: str = "config/google-service-account.json"

    # ── S3 / MinIO ───────────────────────────────────────────
    S3_ENDPOINT: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET_RECORDINGS: str = "recordings"
    S3_BUCKET_EXPORTS: str = "exports"
    S3_REGION: str = "us-east-1"
    S3_USE_SSL: bool = False

    # ── Sentry ───────────────────────────────────────────────
    SENTRY_DSN: str = ""

    # ── CORS ─────────────────────────────────────────────────
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache()
def get_settings() -> Settings:
    return Settings()
