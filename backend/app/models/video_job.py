from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    ARRAY,
    JSON,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

# Status flow: queued → generating → pending_approval → approved → uploading → posted → failed
VIDEO_JOB_STATUSES = (
    "queued",
    "generating",
    "pending_approval",
    "approved",
    "uploading",
    "posted",
    "failed",
    "rejected",
)

# How the script was obtained.
SCRIPT_SOURCES = ("manual", "seed", "ai")


class VideoJob(Base):
    __tablename__ = "video_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    channel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("youtube_channels.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # ---- Generation configuration --------------------------------------
    genre: Mapped[str] = mapped_column(String(50), nullable=False, default="horror")
    duration_tier: Mapped[str] = mapped_column(String(10), nullable=False, default="30s")
    model_tier: Mapped[str] = mapped_column(String(20), nullable=False, default="Lite")
    script_source: Mapped[str] = mapped_column(String(20), nullable=False, default="ai")

    status: Mapped[str] = mapped_column(
        String(50), default="queued", nullable=False, index=True
    )

    # ---- Content -------------------------------------------------------
    topic: Mapped[str | None] = mapped_column(Text, nullable=True)   # seed/idea
    script: Mapped[str | None] = mapped_column(Text, nullable=True)  # final narration
    scene_plan: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # scenes + image prompts
    word_timestamps: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # for captions
    seo_title: Mapped[str | None] = mapped_column(String(100), nullable=True)
    seo_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    seo_tags: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)

    # ---- Voice ---------------------------------------------------------
    voice_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    voice_settings: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # ---- Output --------------------------------------------------------
    video_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    youtube_video_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    youtube_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ---- Accounting ----------------------------------------------------
    credits_cost: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cost_usd: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)  # internal

    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    approval_token: Mapped[str | None] = mapped_column(
        String(100), nullable=True, index=True
    )
    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    posted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    scheduled_for: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    user: Mapped = relationship("User", back_populates="video_jobs", lazy="noload")
    channel: Mapped = relationship(
        "YoutubeChannel", back_populates="video_jobs", lazy="noload"
    )
    analytics: Mapped[list] = relationship(
        "VideoAnalytic", back_populates="job", lazy="noload"
    )
