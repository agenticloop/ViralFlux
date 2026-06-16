from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select

from app.workers.celery_app import celery_app
from app.core.database import async_session_maker

logger = logging.getLogger(__name__)


@celery_app.task
def sync_analytics():
    """
    Sync YouTube analytics for all posted videos.
    Stores a point-in-time snapshot in the video_analytics table.
    Runs daily via Celery beat (02:00).
    """
    asyncio.run(_sync_analytics_async())


async def _sync_analytics_async() -> None:
    from app.models.video_job import VideoJob
    from app.models.channel import YoutubeChannel
    from app.models.analytics import VideoAnalytic
    from app.services.youtube_service import youtube_service
    from app.core.security import decrypt_token

    async with async_session_maker() as session:
        result = await session.execute(
            select(VideoJob).where(
                VideoJob.status == "posted",
                VideoJob.youtube_video_id.isnot(None),
            )
        )
        jobs = result.scalars().all()

        synced = 0
        failed = 0
        for job in jobs:
            try:
                ch_result = await session.execute(
                    select(YoutubeChannel).where(YoutubeChannel.id == job.channel_id)
                )
                channel = ch_result.scalar_one_or_none()
                if not channel or not channel.oauth_access_token:
                    logger.warning(
                        "Skipping analytics for job %s — no channel or token", job.id
                    )
                    continue

                access_token = decrypt_token(channel.oauth_access_token)
                refresh_token = decrypt_token(channel.oauth_refresh_token)
                stats = await youtube_service.get_video_stats(
                    access_token, refresh_token, job.youtube_video_id
                )

                snapshot = VideoAnalytic(
                    job_id=job.id,
                    youtube_video_id=job.youtube_video_id,
                    views=int(stats.get("views", 0)),
                    likes=int(stats.get("likes", 0)),
                    comments=int(stats.get("comments", 0)),
                    watch_time_hours=stats.get("watch_time_hours", 0),
                    snapshot_at=datetime.now(timezone.utc),
                )
                session.add(snapshot)
                synced += 1

            except Exception as exc:
                logger.warning(
                    "Failed to sync analytics for job %s: %s", job.id, exc
                )
                failed += 1

        await session.commit()
        logger.info(
            "analytics sync complete: %d synced, %d failed out of %d jobs",
            synced,
            failed,
            len(jobs),
        )
