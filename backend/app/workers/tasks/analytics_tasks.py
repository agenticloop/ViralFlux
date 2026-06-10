from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone

from sqlalchemy import select

from app.workers.celery_app import celery_app
from app.core.database import async_session_maker
from app.core.config import settings

logger = logging.getLogger(__name__)


@celery_app.task
def sync_analytics():
    """
    Sync YouTube analytics for all posted videos.
    Stores a point-in-time snapshot in the video_analytics table.
    Called daily by n8n (2 AM cron).
    """
    asyncio.run(_sync_analytics_async())


async def _sync_analytics_async() -> None:
    from app.models.video_job import VideoJob
    from app.models.channel import YoutubeChannel
    from app.models.analytics import VideoAnalytic
    from app.services.youtube_service import YouTubeService
    from app.core.security import decrypt_token

    async with async_session_maker() as session:
        result = await session.execute(
            select(VideoJob).where(
                VideoJob.status == "posted",
                VideoJob.youtube_video_id.isnot(None),
            )
        )
        jobs = result.scalars().all()

        yt = YouTubeService(
            settings.YOUTUBE_CLIENT_ID,
            settings.YOUTUBE_CLIENT_SECRET,
            settings.YOUTUBE_REDIRECT_URI,
        )

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
                stats = await yt.get_video_stats(job.youtube_video_id, access_token)

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


@celery_app.task
def discover_trending_topics():
    """
    Fetch trending horror topics from Reddit, score them via Gemini,
    and cache the ranked list in Redis with a 24-hour TTL.
    Called daily by n8n (6 AM cron).
    """
    asyncio.run(_discover_topics_async())


async def _discover_topics_async() -> None:
    import redis.asyncio as aioredis

    from app.services.reddit_service import RedditService
    from app.services.llm.gemini import GeminiService

    reddit = RedditService(
        settings.REDDIT_CLIENT_ID,
        settings.REDDIT_CLIENT_SECRET,
        settings.REDDIT_USER_AGENT,
    )
    # Fetch top 20 posts; analyse the first 10 to limit LLM cost
    posts = reddit.get_trending_posts(limit=20)

    gemini = GeminiService()
    topics: list[dict] = []

    for post in posts[:10]:
        try:
            result = await gemini.pick_topic([post])
            topics.append(
                {
                    "topic": result.recommended_topic,
                    "source_url": result.source_url,
                    "confidence": result.confidence_score,
                    "reasoning": result.reasoning,
                }
            )
        except Exception as exc:
            logger.warning("Gemini topic scoring failed for post '%s': %s", post.get("title"), exc)
            # Fallback: include the raw Reddit post at lower confidence
            topics.append(
                {
                    "topic": post.get("title", ""),
                    "source_url": post.get("url", ""),
                    "confidence": 0.5,
                    "reasoning": "Reddit hot post (Gemini scoring unavailable)",
                }
            )

    # Sort descending by confidence so consumers get best topics first
    topics.sort(key=lambda t: t["confidence"], reverse=True)

    r = aioredis.from_url(settings.REDIS_URL)
    try:
        await r.setex("trending_topics", 86400, json.dumps(topics))  # 24-hour TTL
        logger.info("Cached %d trending topics in Redis", len(topics))
    finally:
        await r.aclose()
