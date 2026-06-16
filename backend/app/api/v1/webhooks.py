from __future__ import annotations

import logging
import secrets
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import genres as genres_mod
from app.core import pricing
from app.core.config import settings
from app.core.dependencies import get_db
from app.models.channel import YoutubeChannel
from app.models.plan import Plan
from app.models.user import User
from app.models.video_job import VideoJob
from app.services import credit_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def _verify_secret(x_webhook_secret: str | None = Header(default=None)) -> None:
    if x_webhook_secret != settings.APP_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook secret.",
        )


def _enqueue_generate(job_id: UUID) -> None:
    try:
        from app.workers.tasks.video_tasks import generate_video as generate_video_task

        generate_video_task.delay(str(job_id))
    except Exception as exc:  # pragma: no cover - queue best-effort
        logger.error("Failed to enqueue generate_video for job %s: %s", job_id, exc)


class JobCompletePayload(BaseModel):
    job_id: UUID
    status: str
    error_message: str | None = None
    script: str | None = None
    scene_plan: dict | None = None
    word_timestamps: dict | None = None
    seo_title: str | None = None
    seo_description: str | None = None
    seo_tags: list[str] | None = None
    video_path: str | None = None
    youtube_video_id: str | None = None
    youtube_url: str | None = None
    cost_usd: float | None = None


class ScheduleTriggerPayload(BaseModel):
    channel_id: UUID
    # Optional overrides; otherwise we derive sensible defaults from plan + channel.
    duration_tier: str | None = None
    model_tier: str | None = None


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
    if payload.script is not None:
        job.script = payload.script
    if payload.scene_plan is not None:
        job.scene_plan = payload.scene_plan
    if payload.word_timestamps is not None:
        job.word_timestamps = payload.word_timestamps
    if payload.seo_title is not None:
        job.seo_title = payload.seo_title
    if payload.seo_description is not None:
        job.seo_description = payload.seo_description
    if payload.seo_tags is not None:
        job.seo_tags = payload.seo_tags
    if payload.video_path:
        job.video_path = payload.video_path
    if payload.youtube_video_id:
        job.youtube_video_id = payload.youtube_video_id
        job.youtube_url = payload.youtube_url
        job.posted_at = datetime.now(timezone.utc)
    if payload.cost_usd is not None:
        from decimal import Decimal

        job.cost_usd = Decimal(str(payload.cost_usd))

    # Refund credits if the generation failed.
    if payload.status == "failed" and job.credits_cost:
        user_res = await db.execute(select(User).where(User.id == job.user_id))
        user = user_res.scalar_one_or_none()
        if user:
            await credit_service.refund_video(
                db, user, credits=job.credits_cost, model=job.model_tier, job_id=job.id
            )

    await db.flush()
    logger.info("Job %s updated via n8n webhook to status '%s'", payload.job_id, payload.status)
    return {"message": "Job updated.", "job_id": str(payload.job_id)}


@router.post("/n8n/schedule-trigger", dependencies=[Depends(_verify_secret)])
async def n8n_schedule_trigger(
    payload: ScheduleTriggerPayload,
    db: AsyncSession = Depends(get_db),
):
    ch_res = await db.execute(
        select(YoutubeChannel).where(
            YoutubeChannel.id == payload.channel_id,
            YoutubeChannel.is_active == True,  # noqa: E712
        )
    )
    channel = ch_res.scalar_one_or_none()
    if not channel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found.")

    user_res = await db.execute(select(User).where(User.id == channel.user_id))
    user = user_res.scalar_one_or_none()
    if not user or not user.plan_id:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="Owner has no active plan."
        )

    plan_res = await db.execute(select(Plan).where(Plan.id == user.plan_id))
    plan = plan_res.scalar_one_or_none()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="Owner plan not found."
        )

    await credit_service.ensure_period(db, user, plan)

    # Derive defaults from the plan (smallest allowed duration, best allowed model).
    allowed_durations = pricing.PLAN_DURATIONS.get(plan.name, ["20s"])
    allowed_models = pricing.PLAN_MODELS.get(plan.name, ["Lite"])
    duration = payload.duration_tier or allowed_durations[0]
    requested_model = payload.model_tier or allowed_models[-1]

    if duration not in allowed_durations:
        duration = allowed_durations[0]
    if requested_model not in allowed_models:
        requested_model = allowed_models[-1]

    genre = channel.genre if channel.genre in pricing.PLAN_GENRES.get(plan.name, []) else (
        pricing.PLAN_GENRES.get(plan.name, ["horror"])[0]
    )

    effective_model, fell_back = await credit_service.resolve_model_tier(
        db, user, plan, requested_model
    )
    credits = pricing.credits_for_video(duration, effective_model)
    if not credit_service.can_afford(user, credits):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={"message": "Owner has insufficient credits.", "needed": credits,
                    "balance": credit_service.balance(user)},
        )

    genre_def = genres_mod.get_genre(genre)
    job = VideoJob(
        user_id=user.id,
        channel_id=channel.id,
        genre=genre,
        duration_tier=duration,
        model_tier=effective_model,
        script_source="ai",
        voice_id=genre_def["default_voice_id"],
        voice_settings=genre_def["voice_settings"],
        credits_cost=credits,
        approval_token=secrets.token_urlsafe(32),
        status="queued",
    )
    db.add(job)
    await db.flush()

    await credit_service.reserve_for_video(
        db, user, duration=duration, model=effective_model, job_id=job.id
    )

    _enqueue_generate(job.id)

    logger.info(
        "Schedule trigger for channel %s → queued job %s (%s %s, fell_back=%s)",
        payload.channel_id, job.id, duration, effective_model, fell_back,
    )
    return {
        "message": "Generation queued.",
        "job_id": str(job.id),
        "credits_charged": credits,
        "fell_back_to_balanced": fell_back,
    }
