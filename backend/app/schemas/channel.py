from __future__ import annotations

from datetime import datetime, time
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class ChannelCreate(BaseModel):
    channel_name: str
    genre: str = "horror"
    seed_prompt: str | None = None
    voice_id: str | None = None
    voice_name: str | None = None
    default_model_tier: str = "Lite"
    default_duration: str = "30s"
    music_bucket: str | None = None


class ChannelUpdate(BaseModel):
    channel_name: str | None = None
    genre: str | None = None
    seed_prompt: str | None = None
    voice_id: str | None = None
    voice_name: str | None = None
    default_model_tier: str | None = None
    default_duration: str | None = None
    music_bucket: str | None = None


class ScheduleConfig(BaseModel):
    is_enabled: bool = False
    frequency_days: int = 2
    post_time: time = time(18, 0)
    timezone: str = "America/Los_Angeles"
    require_approval: bool = True
    approval_email: EmailStr | None = None
    topics_queue: list[str] | None = None


class ScheduleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    channel_id: UUID
    is_enabled: bool
    frequency_days: int
    post_time: time
    timezone: str
    require_approval: bool
    approval_email: str | None
    block_ends_at: datetime | None
    last_run_at: datetime | None
    next_run_at: datetime | None
    topics_queue: list[str] | None
    created_at: datetime


class ChannelOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    channel_name: str

    # Content configuration
    genre: str
    seed_prompt: str | None = None
    seed_prompt_updated_at: datetime | None = None
    default_model_tier: str
    default_duration: str
    voice_id: str
    voice_name: str | None = None
    music_bucket: str

    # YouTube connection (direct multi-account OAuth)
    youtube_connected: bool
    youtube_channel_id: str | None = None
    youtube_channel_title: str | None = None
    youtube_thumbnail_url: str | None = None
    google_account_email: str | None = None
    oauth_expiry: datetime | None = None

    is_active: bool
    created_at: datetime

    # Nested schedule if loaded
    schedule: ScheduleOut | None = None
