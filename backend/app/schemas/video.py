from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class VideoGenerateRequest(BaseModel):
    channel_id: UUID
    genre: str | None = None
    duration_tier: str
    model_tier: str
    script_source: str = "ai"
    # For script_source == "manual": the full narration text.
    script: str | None = None
    # For script_source in ("seed", "ai"): an idea/seed/topic.
    topic: str | None = None
    seed: str | None = None
    voice_id: str | None = None
    schedule_for: datetime | None = None


class VideoJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    channel_id: UUID
    genre: str
    duration_tier: str
    model_tier: str
    script_source: str
    status: str
    topic: str | None
    script: str | None
    scene_plan: dict | None
    word_timestamps: dict | None
    seo_title: str | None
    seo_description: str | None
    seo_tags: list[str] | None
    voice_id: str | None
    voice_settings: dict | None
    video_path: str | None
    youtube_video_id: str | None
    youtube_url: str | None
    credits_cost: int
    cost_usd: Decimal | None
    error_message: str | None
    approval_token: str | None
    approved_at: datetime | None
    posted_at: datetime | None
    scheduled_for: datetime | None
    created_at: datetime
    updated_at: datetime


class VideoGenerateResponse(BaseModel):
    """Returned by /generate and /bulk-generate items: the job plus billing info."""

    job: VideoJobOut
    credits_charged: int
    fell_back_to_balanced: bool


class VideoApproveRequest(BaseModel):
    note: str | None = None


class VideoBulkGenerateItem(BaseModel):
    genre: str | None = None
    duration_tier: str
    model_tier: str
    script_source: str = "ai"
    script: str | None = None
    topic: str | None = None
    seed: str | None = None
    voice_id: str | None = None


class VideoBulkGenerateRequest(BaseModel):
    channel_id: UUID
    items: list[VideoBulkGenerateItem]


class VideoListResponse(BaseModel):
    items: list[VideoJobOut]
    total: int
    page: int
    page_size: int
