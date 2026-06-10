"""Initial schema — all tables

Revision ID: 001
Revises:
Create Date: 2025-01-01 00:00:00

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── plans ────────────────────────────────────────────────────────────────
    op.create_table(
        "plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(50), nullable=False, unique=True),
        sa.Column("price_usd", sa.Numeric(10, 2), nullable=False),
        sa.Column("shorts_per_month", sa.Integer(), nullable=True),
        sa.Column("channels_limit", sa.Integer(), nullable=True),
        sa.Column("features", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("stripe_price_id", sa.String(255), nullable=True),
    )

    # ── users ────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "plan_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("plans.id"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_users_email", "users", ["email"])

    # ── youtube_channels ─────────────────────────────────────────────────────
    op.create_table(
        "youtube_channels",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("channel_name", sa.String(255), nullable=False),
        sa.Column("youtube_channel_id", sa.String(100), nullable=True),
        sa.Column("oauth_access_token", sa.Text(), nullable=True),
        sa.Column("oauth_refresh_token", sa.Text(), nullable=True),
        sa.Column("oauth_expiry", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "default_voice_provider",
            sa.String(50),
            nullable=False,
            server_default="edge-tts",
        ),
        sa.Column(
            "default_voice_id",
            sa.String(100),
            nullable=False,
            server_default="en-US-GuyNeural",
        ),
        sa.Column(
            "default_music_category",
            sa.String(50),
            nullable=False,
            server_default="horror_ambient",
        ),
        sa.Column(
            "default_format",
            sa.String(50),
            nullable=False,
            server_default="horror_story",
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_youtube_channels_user_id", "youtube_channels", ["user_id"])

    # ── channel_schedules ────────────────────────────────────────────────────
    op.create_table(
        "channel_schedules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "channel_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("youtube_channels.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("frequency_days", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("post_time", sa.Time(), nullable=False, server_default="18:00:00"),
        sa.Column(
            "timezone",
            sa.String(50),
            nullable=False,
            server_default="America/Los_Angeles",
        ),
        sa.Column("require_approval", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("approval_email", sa.String(255), nullable=True),
        sa.Column("auto_topic", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "topics_queue",
            postgresql.ARRAY(sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # ── content_formats ──────────────────────────────────────────────────────
    op.create_table(
        "content_formats",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(50), nullable=False, unique=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "config_schema",
            postgresql.JSON(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "min_plan",
            sa.String(50),
            nullable=False,
            server_default="starter",
        ),
    )

    # ── video_jobs ───────────────────────────────────────────────────────────
    op.create_table(
        "video_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "channel_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("youtube_channels.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("format_slug", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="queued"),
        sa.Column("topic", sa.Text(), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("script", sa.Text(), nullable=True),
        sa.Column("seo_title", sa.String(100), nullable=True),
        sa.Column("seo_description", sa.Text(), nullable=True),
        sa.Column("seo_tags", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("voice_provider", sa.String(50), nullable=True),
        sa.Column("voice_id", sa.String(100), nullable=True),
        sa.Column("video_path", sa.Text(), nullable=True),
        sa.Column("youtube_video_id", sa.String(50), nullable=True),
        sa.Column("youtube_url", sa.Text(), nullable=True),
        sa.Column("cost_usd", sa.Numeric(10, 4), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("approval_token", sa.String(100), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scheduled_for", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_video_jobs_user_id", "video_jobs", ["user_id"])
    op.create_index("ix_video_jobs_channel_id", "video_jobs", ["channel_id"])
    op.create_index("ix_video_jobs_status", "video_jobs", ["status"])
    op.create_index("ix_video_jobs_approval_token", "video_jobs", ["approval_token"])

    # ── assets ───────────────────────────────────────────────────────────────
    op.create_table(
        "assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("type", sa.String(30), nullable=False),
        sa.Column("category", sa.String(50), nullable=True),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("license", sa.String(50), nullable=False, server_default="cc0"),
        sa.Column("tags", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_assets_type", "assets", ["type"])
    op.create_index("ix_assets_category", "assets", ["category"])

    # ── blog_posts ───────────────────────────────────────────────────────────
    op.create_table(
        "blog_posts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "author_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), nullable=False, unique=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("excerpt", sa.Text(), nullable=True),
        sa.Column("meta_title", sa.String(255), nullable=True),
        sa.Column("meta_description", sa.String(300), nullable=True),
        sa.Column("og_image_url", sa.Text(), nullable=True),
        sa.Column("featured_image_url", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("tags", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("reading_time_min", sa.Integer(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_blog_posts_slug", "blog_posts", ["slug"])
    op.create_index("ix_blog_posts_status", "blog_posts", ["status"])

    # ── video_analytics ──────────────────────────────────────────────────────
    op.create_table(
        "video_analytics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "job_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("video_jobs.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("youtube_video_id", sa.String(50), nullable=True),
        sa.Column("views", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("likes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("comments", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("watch_time_hours", sa.Numeric(10, 2), nullable=True),
        sa.Column(
            "snapshot_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_video_analytics_job_id", "video_analytics", ["job_id"])


def downgrade() -> None:
    op.drop_table("video_analytics")
    op.drop_table("blog_posts")
    op.drop_table("assets")
    op.drop_table("video_jobs")
    op.drop_table("content_formats")
    op.drop_table("channel_schedules")
    op.drop_table("youtube_channels")
    op.drop_table("users")
    op.drop_table("plans")
