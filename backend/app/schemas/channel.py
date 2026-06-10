from __future__ import annotations

from datetime import datetime, time
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class ChannelCreate(BaseModel):
    channel_name: str
    default_voice_provider: str = "edge-tts"
    default_voice_id: str = "en-US-GuyNeural"
    default_music_category: str = "horror_ambient"
    default_format: str = "horror_story"


class ChannelUpdate(BaseModel):
    channel_name: str | None = None
    default_voice_provider: str | None = None
    default_voice_id: str | None = None
    default_music_category: str | None = None
    default_format: str | None = None


class ChannelOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    channel_name: str
    youtube_channel_id: str | None
    oauth_expiry: datetime | None
    default_voice_provider: str
    default_voice_id: str
    default_music_category: str
    default_format: str
    is_active: bool
    created_at: datetime
    # Nested schedule if loaded
    schedule: ScheduleOut | None = None


class ScheduleConfig(BaseModel):
    is_enabled: bool = False
    frequency_days: int = 2
    post_time: time = time(18, 0)
    timezone: str = "America/Los_Angeles"
    require_approval: bool = True
    approval_email: EmailStr | None = None
    auto_topic: bool = True
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
    auto_topic: bool
    topics_queue: list[str] | None
    created_at: datetime
