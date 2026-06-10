from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App
    APP_ENV: str = "development"
    APP_SECRET_KEY: str = "changeme-insecure-secret"
    APP_URL: str = "http://localhost"
    TIMEZONE: str = "America/Los_Angeles"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://viralflux:viralflux@localhost:5432/viralflux"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # JWT
    JWT_SECRET_KEY: str = "changeme-jwt-secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Resend (transactional email)
    RESEND_API_KEY: str = ""
    EMAIL_FROM: str = "ViralFlux <noreply@skypulseforge.com>"

    # LLMs
    GOOGLE_AI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash-lite"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    # TTS
    ELEVENLABS_API_KEY: str = ""
    GOOGLE_TTS_API_KEY: str = ""

    # Media APIs
    PEXELS_API_KEY: str = ""
    PIXABAY_API_KEY: str = ""
    UNSPLASH_ACCESS_KEY: str = ""

    # YouTube OAuth
    YOUTUBE_CLIENT_ID: str = ""
    YOUTUBE_CLIENT_SECRET: str = ""
    YOUTUBE_REDIRECT_URI: str = ""

    # Reddit
    REDDIT_CLIENT_ID: str = ""
    REDDIT_CLIENT_SECRET: str = ""
    REDDIT_USER_AGENT: str = "ViralFlux/1.0"

    # Stripe
    STRIPE_SECRET_KEY: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""

    # n8n
    N8N_USER: str = "admin"
    N8N_PASSWORD: str = ""
    N8N_WEBHOOK_URL: str = ""

    # Video
    FFMPEG_PATH: str = "/usr/bin/ffmpeg"
    WHISPER_MODEL: str = "base"
    MAX_VIDEO_DURATION_SEC: int = 60
    VIDEO_RESOLUTION: str = "1080x1920"

    # Storage
    MEDIA_DIR: str = "/app/media"
    ASSETS_DIR: str = "/app/assets"
    MAX_STORAGE_GB: int = 50

    # Encryption key for OAuth tokens (Fernet key — 32-byte base64url)
    ENCRYPTION_KEY: str = ""

    # Admin emails (comma-separated)
    ADMIN_EMAILS: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def admin_email_list(self) -> list[str]:
        return [e.strip() for e in self.ADMIN_EMAILS.split(",") if e.strip()]


settings = Settings()
