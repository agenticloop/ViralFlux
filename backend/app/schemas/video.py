from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class VideoGenerateRequest(BaseModel):
    channel_id: UUID
    topic: str | None = None
    format: str | None = None
    voice_provider: str | None = None
    voice_id: str | None = None
    schedule_for: datetime | None = None


class VideoJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    channel_id: UUID
    format_slug: str
    status: str
    topic: str | None
    source_url: str | None
    script: str | None
    seo_title: str | None
    seo_description: str | None
    seo_tags: list[str] | None
    voice_provider: str | None
    voice_id: str | None
    video_path: str | None
    youtube_video_id: str | None
    youtube_url: str | None
    cost_usd: Decimal | None
    error_message: str | None
    approval_token: str | None
    approved_at: datetime | None
    posted_at: datetime | None
    scheduled_for: datetime | None
    created_at: datetime
    updated_at: datetime


class VideoApproveRequest(BaseModel):
    note: str | None = None


class VideoBulkGenerateRequest(BaseModel):
    channel_id: UUID
    count: int = 1
    format: str | None = None
    topic_list: list[str] | None = None


class VideoListResponse(BaseModel):
    items: list[VideoJobOut]
    total: int
    page: int
    page_size: int
