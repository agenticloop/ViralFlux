from __future__ import annotations

import uuid
from datetime import datetime, time

from sqlalchemy import (
    ARRAY,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class YoutubeChannel(Base):
    __tablename__ = "youtube_channels"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    channel_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # ---- Direct YouTube OAuth (our own app, multi-Google-account) -------
    # Each channel stores its OWN Google account's encrypted tokens, so a
    # single user can connect channels across several Google accounts.
    youtube_channel_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    youtube_channel_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    youtube_thumbnail_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    google_account_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    oauth_access_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    oauth_refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    oauth_expiry: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    oauth_state: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)

    # ---- Content configuration -----------------------------------------
    genre: Mapped[str] = mapped_column(String(50), default="horror", nullable=False)
    seed_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    seed_prompt_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    default_model_tier: Mapped[str] = mapped_column(
        String(20), default="Lite", nullable=False
    )
    default_duration: Mapped[str] = mapped_column(String(10), default="30s", nullable=False)
    voice_id: Mapped[str] = mapped_column(
        String(100), default="pqHfZKP75CvOlQylNhV4", nullable=False
    )
    voice_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    music_bucket: Mapped[str] = mapped_column(
        String(50), default="horror_ambient", nullable=False
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    user: Mapped = relationship("User", back_populates="channels", lazy="noload")
    schedule: Mapped | None = relationship(
        "ChannelSchedule",
        back_populates="channel",
        uselist=False,
        lazy="noload",
    )
    video_jobs: Mapped[list] = relationship(
        "VideoJob", back_populates="channel", lazy="noload"
    )

    @property
    def youtube_connected(self) -> bool:
        return bool(self.oauth_refresh_token)


class ChannelSchedule(Base):
    __tablename__ = "channel_schedules"

    __table_args__ = (UniqueConstraint("channel_id", name="uq_channel_schedules_channel_id"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    channel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("youtube_channels.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    frequency_days: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    post_time: Mapped[time] = mapped_column(Time, default=time(18, 0), nullable=False)
    timezone: Mapped[str] = mapped_column(
        String(50), default="America/Los_Angeles", nullable=False
    )
    require_approval: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    approval_email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Free plan: one fixed-length block with manual renewal; paid: continuous.
    block_ends_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_run_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    next_run_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    # Optional explicit topic/seed queue to consume before falling back to the
    # channel's weekly seed prompt.
    topics_queue: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    channel: Mapped = relationship(
        "YoutubeChannel", back_populates="schedule", lazy="noload"
    )
