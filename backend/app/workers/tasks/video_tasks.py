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


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def generate_video(self, job_id: str):
    """
    Main video generation task.

    Steps:
    1. Load job from DB, set status=generating
    2. Load channel config
    3. Run format plugin to get FormatOutput
    4. Run VideoPipeline.run()
    5. Set job.video_path, status=pending_approval
    6. If channel schedule requires_approval: send approval email
    7. Else: auto-trigger upload_video task

    On error: set status=failed, error_message, retry up to 3x.
    """
    try:
        asyncio.run(_generate_video_async(job_id))
    except Exception as exc:
        logger.exception("generate_video task failed for job %s: %s", job_id, exc)
        raise self.retry(exc=exc)


async def _generate_video_async(job_id: str) -> None:
    async with async_session_maker() as session:
        # --- load job ---
        result = await session.execute(
            select(VideoJob).where(VideoJob.id == uuid.UUID(job_id))
        )
        job = result.scalar_one_or_none()
        if not job:
            logger.error("Job %s not found in DB — aborting", job_id)
            return

        # --- load channel ---
        ch_result = await session.execute(
            select(YoutubeChannel).where(YoutubeChannel.id == job.channel_id)
        )
        channel = ch_result.scalar_one_or_none()

        try:
            # Mark as generating
            job.status = "generating"
            await session.commit()

            # --- resolve format plugin ---
            from app.services.formats.registry import get_format_plugin

            fmt = get_format_plugin(job.format_slug)

            # Build channel-level voice config (can be overridden per-job)
            channel_config: dict = {
                "voice_provider": channel.default_voice_provider,
                "voice_id": channel.default_voice_id,
                "music_category": channel.default_music_category,
            }
            if job.voice_provider:
                channel_config["voice_provider"] = job.voice_provider
            if job.voice_id:
                channel_config["voice_id"] = job.voice_id

            # --- run format plugin (generates script, SEO, cost estimate) ---
            fmt_output = await fmt.prepare(job.topic, channel_config)

            # Persist script & SEO back to job
            job.script = fmt_output.script
            job.seo_title = fmt_output.seo_title
            job.seo_description = fmt_output.seo_description
            job.seo_tags = fmt_output.seo_tags
            job.cost_usd = fmt_output.cost_estimate_usd
            job.voice_provider = fmt_output.voice_provider
            job.voice_id = fmt_output.voice_id
            await session.commit()

            # --- run video assembly pipeline ---
            from app.services.video.pipeline import VideoPipeline

            pipeline = VideoPipeline(settings, session)
            video_path = await pipeline.run(job)

            # --- update job post-render ---
            job.video_path = video_path
            job.status = "pending_approval"
            job.approval_token = secrets.token_urlsafe(32)
            await session.commit()

            # --- route approval ---
            sched_result = await session.execute(
                select(ChannelSchedule).where(ChannelSchedule.channel_id == channel.id)
            )
            schedule = sched_result.scalar_one_or_none()

            require_approval: bool = schedule.require_approval if schedule else True

            if require_approval and schedule and schedule.approval_email:
                from app.services.email_service import EmailService

                email_svc = EmailService(
                    settings.SMTP_HOST,
                    settings.SMTP_PORT,
                    settings.SMTP_USER,
                    settings.SMTP_PASSWORD,
                    settings.SMTP_FROM_NAME,
                    settings.SMTP_FROM_EMAIL,
                )
                preview_url = f"{settings.APP_URL}/media/previews/{job_id}.mp4"
                await email_svc.send_approval_request(
                    schedule.approval_email,
                    job_id,
                    job.approval_token,
                    preview_url,
                )
                logger.info("Approval email sent for job %s", job_id)
            elif not require_approval:
                # Auto-approve and queue upload immediately
                job.status = "approved"
                job.approved_at = datetime.now(timezone.utc)
                await session.commit()
                upload_to_youtube.delay(job_id)
                logger.info("Job %s auto-approved, upload task queued", job_id)

        except Exception as exc:
            logger.exception("Job %s failed during generation: %s", job_id, exc)
            job.status = "failed"
            job.error_message = str(exc)
            await session.commit()
            raise


@celery_app.task(bind=True, max_retries=3, default_retry_delay=120)
def upload_to_youtube(self, job_id: str):
    """Upload an approved video to YouTube and update job status to posted."""
    try:
        asyncio.run(_upload_async(job_id))
    except Exception as exc:
        logger.exception("upload_to_youtube task failed for job %s: %s", job_id, exc)
        raise self.retry(exc=exc)


async def _upload_async(job_id: str) -> None:
    async with async_session_maker() as session:
        result = await session.execute(
            select(VideoJob).where(VideoJob.id == uuid.UUID(job_id))
        )
        job = result.scalar_one_or_none()
        if not job or job.status != "approved":
            logger.warning(
                "upload_to_youtube: job %s not found or not in approved state (status=%s)",
                job_id,
                getattr(job, "status", "N/A"),
            )
            return

        ch_result = await session.execute(
            select(YoutubeChannel).where(YoutubeChannel.id == job.channel_id)
        )
        channel = ch_result.scalar_one_or_none()

        try:
            job.status = "uploading"
            await session.commit()

            from app.core.security import decrypt_token
            from app.services.youtube_service import YouTubeService

            yt = YouTubeService(
                settings.YOUTUBE_CLIENT_ID,
                settings.YOUTUBE_CLIENT_SECRET,
                settings.YOUTUBE_REDIRECT_URI,
            )

            access_token = decrypt_token(channel.oauth_access_token)
            refresh_token = decrypt_token(channel.oauth_refresh_token)

            scheduled_time: str | None = None
            if job.scheduled_for:
                scheduled_time = job.scheduled_for.isoformat()

            video_id = await yt.upload_video(
                job.video_path,
                job.seo_title,
                job.seo_description,
                job.seo_tags,
                access_token,
                refresh_token,
                scheduled_time,
            )

            job.youtube_video_id = video_id
            job.youtube_url = f"https://youtube.com/shorts/{video_id}"
            job.status = "posted"
            job.posted_at = datetime.now(timezone.utc)
            await session.commit()
            logger.info("Job %s posted successfully as YouTube video %s", job_id, video_id)

        except Exception as exc:
            logger.exception("Upload failed for job %s: %s", job_id, exc)
            job.status = "failed"
            job.error_message = f"Upload failed: {exc}"
            await session.commit()
            raise
