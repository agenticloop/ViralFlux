from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    plan_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("plans.id"), nullable=True
    )

    # ---- Credit wallet (see app/services/credit_service.py) -------------
    # subscription_credits reset each billing period (Pro/Agency: 1-mo rollover).
    # topup_credits never expire while the account is active.
    subscription_credits: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    topup_credits: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_quota_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    credits_period_start: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    credits_period_end: Mapped[datetime | None] = mapped_column(
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
    plan: Mapped | None = relationship("Plan", back_populates="users", lazy="noload")
    channels: Mapped[list] = relationship(
        "YoutubeChannel", back_populates="user", lazy="noload"
    )
    video_jobs: Mapped[list] = relationship(
        "VideoJob", back_populates="user", lazy="noload"
    )
    blog_posts: Mapped[list] = relationship(
        "BlogPost", back_populates="author", lazy="noload"
    )
    credit_transactions: Mapped[list] = relationship(
        "CreditTransaction", back_populates="user", lazy="noload"
    )
    addons: Mapped[list] = relationship(
        "AddonSubscription", back_populates="user", lazy="noload"
    )

    @property
    def total_credits(self) -> int:
        return self.subscription_credits + self.topup_credits
