from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ------------------------------------------------------------------ App
    APP_ENV: str = "development"
    APP_SECRET_KEY: str = "changeme-insecure-secret"
    APP_URL: str = "http://localhost"
    FRONTEND_URL: str = "http://localhost:3000"
    TIMEZONE: str = "America/Los_Angeles"

    # ------------------------------------------------------------- Database
    DATABASE_URL: str = "postgresql+asyncpg://viralflux:viralflux@localhost:5432/viralflux"

    # ---------------------------------------------------------------- Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # ------------------------------------------------------------------ JWT
    JWT_SECRET_KEY: str = "changeme-jwt-secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ------------------------------------------------ Resend (email, kept)
    RESEND_API_KEY: str = ""
    EMAIL_FROM: str = "ViralFlux <noreply@skypulseforge.com>"

    # ------------------------------------------------ LLM (Gemini ONLY)
    # Three UI tiers (Lite / Balanced / Max) map to three configurable Gemini
    # model IDs. Defaults reflect the intended model stack from plan.md; they
    # are env-overridable so the underlying model can swap without code change.
    GOOGLE_AI_API_KEY: str = ""
    GEMINI_MODEL_LITE: str = "gemini-3.1-flash-lite"
    GEMINI_MODEL_BALANCED: str = "gemini-3.1-flash"
    GEMINI_MODEL_MAX: str = "gemini-3.5-flash"

    # ------------------------------------------------ TTS (ElevenLabs ONLY)
    ELEVENLABS_API_KEY: str = ""
    ELEVENLABS_MODEL: str = "eleven_flash_v2_5"
    ELEVENLABS_BASE_URL: str = "https://api.elevenlabs.io"

    # ------------------------------------------------ Image generation
    # Provider-agnostic. Default Imagen 4 Fast on the Google AI Studio key.
    # Swap to z-image / gpt-image-mini by changing IMAGE_PROVIDER + key.
    IMAGE_PROVIDER: str = "imagen"  # imagen | zimage | gptimage
    IMAGEN_MODEL: str = "imagen-4.0-fast-generate-001"

    # ------------------------------------------------ YouTube (direct OAuth)
    # Our own OAuth app. One user may connect channels living under different
    # Google accounts; tokens stored encrypted per-channel.
    YOUTUBE_CLIENT_ID: str = ""
    YOUTUBE_CLIENT_SECRET: str = ""
    YOUTUBE_REDIRECT_URI: str = "http://localhost:8000/api/v1/channels/youtube/callback"

    # ------------------------------------------------ Stripe (deferred)
    STRIPE_SECRET_KEY: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""

    # ------------------------------------------------ n8n
    N8N_USER: str = "admin"
    N8N_PASSWORD: str = ""
    N8N_WEBHOOK_URL: str = ""

    # ------------------------------------------------ Video processing
    FFMPEG_PATH: str = "/usr/bin/ffmpeg"
    FFPROBE_PATH: str = "/usr/bin/ffprobe"
    WHISPER_MODEL: str = "base"  # caption fallback only; EL timestamps primary
    VIDEO_RESOLUTION: str = "1080x1920"

    # ------------------------------------------------ Storage
    MEDIA_DIR: str = "/app/media"
    ASSETS_DIR: str = "/app/assets"
    MAX_STORAGE_GB: int = 50

    # ------------------------------------------------ Encryption (Fernet)
    ENCRYPTION_KEY: str = ""

    # ------------------------------------------------ Admin
    ADMIN_EMAILS: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def admin_email_list(self) -> list[str]:
        return [e.strip() for e in self.ADMIN_EMAILS.split(",") if e.strip()]

    def gemini_model_for_tier(self, tier: str) -> str:
        """Resolve a UI model tier (Lite/Balanced/Max) to a real Gemini model id."""
        return {
            "Lite": self.GEMINI_MODEL_LITE,
            "Balanced": self.GEMINI_MODEL_BALANCED,
            "Max": self.GEMINI_MODEL_MAX,
        }.get(tier, self.GEMINI_MODEL_LITE)


settings = Settings()
