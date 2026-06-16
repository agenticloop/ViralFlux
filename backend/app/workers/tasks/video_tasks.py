from __future__ import annotations

import asyncio
import logging
import secrets
import uuid
from datetime import datetime, timezone

from sqlalchemy import select

from app.workers.celery_app import celery_app
from app.core.database import async_session_maker
from app.core.config import settings
from app.models.video_job import VideoJob
from app.models.channel import YoutubeChannel, ChannelSchedule

logger = logging.getLogger(__name__)


class _AlreadyHandled(Exception):
    """Internal: signals the failure was already persisted and refunded."""


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def generate_video(self, job_id: str):
    """Generate a video end-to-end: format prep → render → approval routing.

    On any failure the reserved credits are refunded exactly once and the job
    is marked failed; the task is NOT retried after a refund.
    """
    try:
        asyncio.run(_generate_video_async(job_id))
    except _AlreadyHandled:
        # Failure was persisted + refunded inside the coroutine; do not retry.
        return
    except Exception as exc:
        logger.exception("generate_video task failed for job %s: %s", job_id, exc)
        raise self.retry(exc=exc)


async def _generate_video_async(job_id: str) -> None:
    async with async_session_maker() as session:
        result = await session.execute(
            select(VideoJob).where(VideoJob.id == uuid.UUID(job_id))
        )
        job = result.scalar_one_or_none()
        if not job:
            logger.error("Job %s not found in DB — aborting", job_id)
            return

        ch_result = await session.execute(
            select(YoutubeChannel).where(YoutubeChannel.id == job.channel_id)
        )
        channel = ch_result.scalar_one_or_none()

        try:
            job.status = "generating"
            await session.commit()

            # --- resolve format plugin (format == genre) ---
            from app.services.formats import get_format_plugin

            fmt = await get_format_plugin(job.genre).prepare(job, channel)

            # --- render ---
            from app.services.video.pipeline import VideoPipeline

            result_data = await VideoPipeline().run(job, channel, fmt)

            # --- persist generation results ---
            job.script = fmt.script
            job.scene_plan = {"scenes": fmt.scenes, "image_prompts": fmt.image_prompts}
            job.seo_title = fmt.seo_title
            job.seo_description = fmt.seo_description
            job.seo_tags = fmt.seo_tags
            job.voice_id = fmt.voice_id
            job.voice_settings = fmt.voice_settings
            job.word_timestamps = {"words": result_data.get("word_timestamps", [])}
            job.video_path = result_data["video_path"]
            job.cost_usd = result_data["cost_usd"]
            job.approval_token = secrets.token_urlsafe(32)
            await session.commit()

            # --- approval routing ---
            sched_result = await session.execute(
                select(ChannelSchedule).where(ChannelSchedule.channel_id == channel.id)
            )
            schedule = sched_result.scalar_one_or_none()
            require_approval = schedule.require_approval if schedule else True

            if require_approval:
                job.status = "pending_approval"
                await session.commit()
                await _maybe_send_approval_email(job_id, job, schedule)
                logger.info("Job %s pending approval", job_id)
            else:
                job.status = "approved"
                job.approved_at = datetime.now(timezone.utc)
                await session.commit()
                upload_to_youtube.delay(job_id)
                logger.info("Job %s auto-approved; upload queued", job_id)

        except Exception as exc:
            logger.exception("Job %s failed during generation: %s", job_id, exc)
            job.status = "failed"
            job.error_message = str(exc)[:1000]
            await session.commit()
            await _refund_once(session, job)
            raise _AlreadyHandled() from exc


async def _refund_once(session, job) -> None:
    """Refund reserved credits for a failed job exactly once."""
    credits = int(getattr(job, "credits_cost", 0) or 0)
    if credits <= 0:
        return
    try:
        from app.models.user import User
        from app.services import credit_service

        u_result = await session.execute(select(User).where(User.id == job.user_id))
        user = u_result.scalar_one_or_none()
        if not user:
            return
        await credit_service.refund_video(
            session, user, credits=credits, model=job.model_tier, job_id=job.id
        )
        await session.commit()
        logger.info("Refunded %d credits for failed job %s", credits, job.id)
    except Exception as exc:
        logger.error("Refund failed for job %s: %s", job.id, exc)


async def _maybe_send_approval_email(job_id, job, schedule) -> None:
    if not (schedule and getattr(schedule, "approval_email", None)):
        return
    try:
        from app.services.email_service import EmailService

        email_svc = EmailService()
        preview_url = f"{settings.APP_URL}/media/previews/{job_id}.mp4"
        await email_svc.send_approval_request(
            schedule.approval_email, job_id, job.approval_token, preview_url
        )
        logger.info("Approval email sent for job %s", job_id)
    except Exception as exc:
        logger.warning("Approval email failed for job %s (non-fatal): %s", job_id, exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=120)
def upload_to_youtube(self, job_id: str):
    """Upload an approved video to YouTube via the direct YouTube API."""
    try:
        asyncio.run(_upload_async(job_id))
    except Exception as exc:
        logger.exception("upload_to_youtube task failed for job %s: %s", job_id, exc)
        raise self.retry(exc=exc)


async def _upload_async(job_id: str) -> None:
    from app.core.security import decrypt_token
    from app.services.youtube_service import youtube_service

    async with async_session_maker() as session:
        result = await session.execute(
            select(VideoJob).where(VideoJob.id == uuid.UUID(job_id))
        )
        job = result.scalar_one_or_none()
        if not job or job.status != "approved":
            logger.warning(
                "upload_to_youtube: job %s not found or not approved (status=%s)",
                job_id,
                getattr(job, "status", "N/A"),
            )
            return

        ch_result = await session.execute(
            select(YoutubeChannel).where(YoutubeChannel.id == job.channel_id)
        )
        channel = ch_result.scalar_one_or_none()

        try:
            if not channel or not channel.youtube_connected:
                raise RuntimeError("Channel is not connected to YouTube.")

            job.status = "uploading"
            await session.commit()

            access_token = decrypt_token(channel.oauth_access_token)
            refresh_token = decrypt_token(channel.oauth_refresh_token)

            res = await youtube_service.upload_video(
                access_token,
                refresh_token,
                job.video_path,
                job.seo_title or "",
                job.seo_description or "",
                job.seo_tags or [],
            )

            job.youtube_video_id = res["video_id"]
            job.youtube_url = res["url"]
            job.status = "posted"
            job.posted_at = datetime.now(timezone.utc)
            await session.commit()
            logger.info("Job %s posted (video_id=%s)", job_id, res["video_id"])

        except Exception as exc:
            logger.exception("Upload failed for job %s: %s", job_id, exc)
            job.status = "failed"
            job.error_message = f"Upload failed: {exc}"[:1000]
            await session.commit()
            raise
