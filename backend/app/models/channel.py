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
    youtube_channel_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    oauth_access_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    oauth_refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    oauth_expiry: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    default_voice_provider: Mapped[str] = mapped_column(
        String(50), default="edge-tts", nullable=False
    )
    default_voice_id: Mapped[str] = mapped_column(
        String(100), default="en-US-GuyNeural", nullable=False
    )
    default_music_category: Mapped[str] = mapped_column(
        String(50), default="horror_ambient", nullable=False
    )
    default_format: Mapped[str] = mapped_column(
        String(50), default="horror_story", nullable=False
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
    auto_topic: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    topics_queue: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    channel: Mapped = relationship(
        "YoutubeChannel", back_populates="schedule", lazy="noload"
    )
