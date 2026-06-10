from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_db
from app.models.video_job import VideoJob

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def _verify_secret(x_webhook_secret: str | None = Header(default=None)) -> None:
    if x_webhook_secret != settings.APP_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook secret.",
        )


class JobCompletePayload(BaseModel):
    job_id: UUID
    status: str
    error_message: str | None = None
    video_path: str | None = None
    youtube_video_id: str | None = None
    youtube_url: str | None = None
    cost_usd: float | None = None


class ScheduleTriggerPayload(BaseModel):
    channel_id: UUID


@router.post("/n8n/job-complete", dependencies=[Depends(_verify_secret)])
async def n8n_job_complete(
    payload: JobCompletePayload,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(VideoJob).where(VideoJob.id == payload.job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")

    job.status = payload.status
    if payload.error_message:
        job.error_message = payload.error_message
    if payload.video_path:
        job.video_path = payload.video_path
    if payload.youtube_video_id:
        job.youtube_video_id = payload.youtube_video_id
        job.youtube_url = payload.youtube_url
        job.posted_at = datetime.now(timezone.utc)
    if payload.cost_usd is not None:
        from decimal import Decimal

        job.cost_usd = Decimal(str(payload.cost_usd))

    await db.flush()
    logger.info("Job %s updated via n8n webhook to status '%s'", payload.job_id, payload.status)
    return {"message": "Job updated.", "job_id": str(payload.job_id)}


@router.post("/n8n/schedule-trigger", dependencies=[Depends(_verify_secret)])
async def n8n_schedule_trigger(
    payload: ScheduleTriggerPayload,
    db: AsyncSession = Depends(get_db),
):
    from app.models.channel import YoutubeChannel

    result = await db.execute(
        select(YoutubeChannel).where(
            YoutubeChannel.id == payload.channel_id,
            YoutubeChannel.is_active == True,  # noqa: E712
        )
    )
    channel = result.scalar_one_or_none()
    if not channel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found.")

    import secrets

    job = VideoJob(
        user_id=channel.user_id,
        channel_id=channel.id,
        format_slug=channel.default_format,
        voice_provider=channel.default_voice_provider,
        voice_id=channel.default_voice_id,
        approval_token=secrets.token_urlsafe(32),
        status="queued",
    )
    db.add(job)
    await db.flush()

    try:
        from app.workers.celery_app import celery_app

        celery_app.send_task("app.workers.tasks.video_tasks.generate_video", args=[str(job.id)])
    except Exception as exc:
        logger.error("Failed to queue Celery task from schedule trigger: %s", exc)

    logger.info(
        "Schedule trigger for channel %s → queued job %s",
        payload.channel_id,
        job.id,
    )
    return {"message": "Generation queued.", "job_id": str(job.id)}
