from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_verified_user, get_db
from app.models.analytics import VideoAnalytic
from app.models.channel import YoutubeChannel
from app.models.credits import CreditTransaction
from app.models.video_job import VideoJob
from app.services import credit_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats")
async def dashboard_stats(
    current_user=Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
):
    # Videos posted (all time).
    posted_result = await db.execute(
        select(func.count()).select_from(VideoJob).where(
            VideoJob.user_id == current_user.id,
            VideoJob.status == "posted",
        )
    )
    videos_posted = posted_result.scalar_one()

    # Total views across all jobs.
    views_result = await db.execute(
        select(func.sum(VideoAnalytic.views))
        .join(VideoJob, VideoAnalytic.job_id == VideoJob.id)
        .where(VideoJob.user_id == current_user.id)
    )
    total_views = views_result.scalar_one() or 0

    # Credits spent in the current billing period.
    period_start = current_user.credits_period_start
    spend_stmt = (
        select(func.coalesce(func.sum(-CreditTransaction.amount), 0))
        .where(
            CreditTransaction.user_id == current_user.id,
            CreditTransaction.kind == "video_spend",
        )
    )
    if period_start is not None:
        spend_stmt = spend_stmt.where(CreditTransaction.created_at >= period_start)
    spend_result = await db.execute(spend_stmt)
    credits_used_this_period = int(spend_result.scalar_one() or 0)

    # Active channels.
    channels_result = await db.execute(
        select(func.count()).select_from(YoutubeChannel).where(
            YoutubeChannel.user_id == current_user.id,
            YoutubeChannel.is_active == True,  # noqa: E712
        )
    )
    active_channels = channels_result.scalar_one()

    return {
        "videos_posted": videos_posted,
        "total_views": int(total_views),
        "credits_balance": credit_service.balance(current_user),
        "credits_used_this_period": credits_used_this_period,
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
            VideoJob.genre,
            VideoJob.duration_tier,
            VideoJob.model_tier,
            VideoJob.credits_cost,
            VideoJob.created_at,
            VideoJob.posted_at,
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
            "genre": r.genre,
            "duration_tier": r.duration_tier,
            "model_tier": r.model_tier,
            "credits_cost": r.credits_cost,
            "created_at": r.created_at.isoformat(),
            "posted_at": r.posted_at.isoformat() if r.posted_at else None,
        }
        for r in rows
    ]


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
        last_job_result = await db.execute(
            select(VideoJob.posted_at, VideoJob.created_at)
            .where(VideoJob.channel_id == ch.id, VideoJob.status == "posted")
            .order_by(VideoJob.posted_at.desc())
            .limit(1)
        )
        last_job = last_job_result.one_or_none()

        total_result = await db.execute(
            select(func.count()).select_from(VideoJob).where(VideoJob.channel_id == ch.id)
        )
        total_videos = total_result.scalar_one()

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
                "last_posted_at": last_job.posted_at.isoformat()
                if last_job and last_job.posted_at
                else None,
                "total_videos": total_videos,
                "avg_views": round(avg_views, 1),
            }
        )

    return {"channels": health}
