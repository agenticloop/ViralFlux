from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_current_verified_user, get_db
from app.models.analytics import VideoAnalytic
from app.models.channel import YoutubeChannel
from app.models.video_job import VideoJob

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats")
async def dashboard_stats(
    current_user=Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    first_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Total posted this month
    posted_result = await db.execute(
        select(func.count()).select_from(VideoJob).where(
            VideoJob.user_id == current_user.id,
            VideoJob.status == "posted",
            VideoJob.posted_at >= first_of_month,
        )
    )
    posted_this_month = posted_result.scalar_one()

    # Total posted all time
    total_posted_result = await db.execute(
        select(func.count()).select_from(VideoJob).where(
            VideoJob.user_id == current_user.id,
            VideoJob.status == "posted",
        )
    )
    total_posted = total_posted_result.scalar_one()

    # Total views (latest snapshot per job)
    views_result = await db.execute(
        select(func.sum(VideoAnalytic.views))
        .join(VideoJob, VideoAnalytic.job_id == VideoJob.id)
        .where(VideoJob.user_id == current_user.id)
    )
    total_views = views_result.scalar_one() or 0

    # Total cost this month
    cost_result = await db.execute(
        select(func.sum(VideoJob.cost_usd)).where(
            VideoJob.user_id == current_user.id,
            VideoJob.created_at >= first_of_month,
        )
    )
    cost_this_month = float(cost_result.scalar_one() or 0)

    # Active channels
    channels_result = await db.execute(
        select(func.count()).select_from(YoutubeChannel).where(
            YoutubeChannel.user_id == current_user.id,
            YoutubeChannel.is_active == True,  # noqa: E712
        )
    )
    active_channels = channels_result.scalar_one()

    return {
        "posted_this_month": posted_this_month,
        "total_posted": total_posted,
        "total_views": int(total_views),
        "cost_this_month_usd": round(cost_this_month, 4),
        "active_channels": active_channels,
    }


@router.get("/activity")
async def recent_activity(
    current_user=Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(
            VideoJob.id,
            VideoJob.status,
            VideoJob.topic,
            VideoJob.seo_title,
            VideoJob.channel_id,
            VideoJob.format_slug,
            VideoJob.created_at,
            VideoJob.posted_at,
            VideoJob.cost_usd,
        )
        .where(VideoJob.user_id == current_user.id)
        .order_by(VideoJob.created_at.desc())
        .limit(20)
    )
    rows = result.all()

    return [
        {
            "id": str(r.id),
            "status": r.status,
            "topic": r.topic,
            "title": r.seo_title,
            "channel_id": str(r.channel_id),
            "format": r.format_slug,
            "created_at": r.created_at.isoformat(),
            "posted_at": r.posted_at.isoformat() if r.posted_at else None,
            "cost_usd": float(r.cost_usd) if r.cost_usd else None,
        }
        for r in rows
    ]


@router.get("/trending-topics")
async def trending_topics(
    current_user=Depends(get_current_verified_user),
):
    """Return AI-suggested topics cached in Redis under key `trending_topics`."""
    redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        raw = await redis.get("trending_topics")
        if raw:
            try:
                topics = json.loads(raw)
                return {"topics": topics, "cached": True}
            except json.JSONDecodeError:
                pass
    except Exception as exc:
        logger.warning("Redis error fetching trending topics: %s", exc)
    finally:
        await redis.aclose()

    # Fallback placeholder
    return {
        "topics": [
            "The Watcher in the Woods",
            "Something Wrong at the Old Mill",
            "I Found My Grandfather's Diary",
            "The Night Shift at Pier 17",
            "She Texted Me from the Grave",
        ],
        "cached": False,
    }


@router.get("/channel-health")
async def channel_health(
    current_user=Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
):
    channels_result = await db.execute(
        select(YoutubeChannel).where(
            YoutubeChannel.user_id == current_user.id,
            YoutubeChannel.is_active == True,  # noqa: E712
        )
    )
    channels = channels_result.scalars().all()

    health = []
    for ch in channels:
        # Last posted job
        last_job_result = await db.execute(
            select(VideoJob.posted_at, VideoJob.created_at)
            .where(VideoJob.channel_id == ch.id, VideoJob.status == "posted")
            .order_by(VideoJob.posted_at.desc())
            .limit(1)
        )
        last_job = last_job_result.one_or_none()

        # Total videos
        total_result = await db.execute(
            select(func.count()).select_from(VideoJob).where(
                VideoJob.channel_id == ch.id
            )
        )
        total_videos = total_result.scalar_one()

        # Avg views
        avg_views_result = await db.execute(
            select(func.avg(VideoAnalytic.views))
            .join(VideoJob, VideoAnalytic.job_id == VideoJob.id)
            .where(VideoJob.channel_id == ch.id)
        )
        avg_views = float(avg_views_result.scalar_one() or 0)

        health.append(
            {
                "channel_id": str(ch.id),
                "channel_name": ch.channel_name,
                "youtube_channel_id": ch.youtube_channel_id,
                "last_posted_at": last_job.posted_at.isoformat() if last_job and last_job.posted_at else None,
                "total_videos": total_videos,
                "avg_views": round(avg_views, 1),
            }
        )

    return {"channels": health}
