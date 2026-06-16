from __future__ import annotations

import logging
import os
import secrets
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import genres as genres_mod
from app.core import pricing
from app.core.config import settings
from app.core.dependencies import get_current_verified_user, get_db
from app.models.channel import YoutubeChannel
from app.models.plan import Plan
from app.models.video_job import SCRIPT_SOURCES, VideoJob
from app.schemas.video import (
    VideoApproveRequest,
    VideoBulkGenerateItem,
    VideoBulkGenerateRequest,
    VideoGenerateRequest,
    VideoGenerateResponse,
    VideoJobOut,
    VideoListResponse,
)
from app.services import credit_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/videos", tags=["videos"])


async def _get_job_or_404(job_id: UUID, user_id: UUID, db: AsyncSession) -> VideoJob:
    result = await db.execute(
        select(VideoJob).where(VideoJob.id == job_id, VideoJob.user_id == user_id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video job not found.")
    return job


async def _load_plan(user, db: AsyncSession) -> Plan:
    if not user.plan_id:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="No active plan. Please subscribe to a plan first.",
        )
    res = await db.execute(select(Plan).where(Plan.id == user.plan_id))
    plan = res.scalar_one_or_none()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED, detail="No active plan found."
        )
    return plan


async def _load_channel(channel_id: UUID, user_id: UUID, db: AsyncSession) -> YoutubeChannel:
    res = await db.execute(
        select(YoutubeChannel).where(
            YoutubeChannel.id == channel_id,
            YoutubeChannel.user_id == user_id,
            YoutubeChannel.is_active == True,  # noqa: E712
        )
    )
    channel = res.scalar_one_or_none()
    if not channel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found.")
    return channel


def _topup_url() -> str:
    return f"{settings.FRONTEND_URL.rstrip('/')}/billing/topup"


def _enqueue_generate(job_id: UUID) -> None:
    try:
        from app.workers.tasks.video_tasks import generate_video as generate_video_task

        generate_video_task.delay(str(job_id))
    except Exception as exc:  # pragma: no cover - queue best-effort
        logger.error("Failed to enqueue generate_video for job %s: %s", job_id, exc)


def _enqueue_upload(job_id: UUID) -> None:
    try:
        from app.workers.tasks.video_tasks import upload_to_youtube

        upload_to_youtube.delay(str(job_id))
    except Exception as exc:  # pragma: no cover - queue best-effort
        logger.error("Failed to enqueue upload_to_youtube for job %s: %s", job_id, exc)


def _validate_generation_inputs(plan: Plan, genre: str, duration: str, model: str) -> None:
    """Validate genre/duration/model are allowed for the plan. Raises 403/400/402."""
    if genre not in genres_mod.GENRE_SLUGS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown genre '{genre}'."
        )
    allowed_genres = pricing.PLAN_GENRES.get(plan.name, [])
    if genre not in allowed_genres:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Genre '{genre}' is not available on the '{plan.name}' plan.",
        )

    if duration not in pricing.DURATION_TIERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown duration tier '{duration}'.",
        )
    allowed_durations = pricing.PLAN_DURATIONS.get(plan.name, [])
    if duration not in allowed_durations:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Duration '{duration}' is not available on the '{plan.name}' plan "
            f"(max {pricing.PLAN_MAX_DURATION.get(plan.name)}).",
        )

    if model not in pricing.MODEL_TIERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown model tier '{model}'."
        )
    allowed_models = pricing.PLAN_MODELS.get(plan.name, [])
    if model not in allowed_models:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Model '{model}' is not available on the '{plan.name}' plan.",
        )


def _validate_manual_script(plan: Plan, script_source: str, script: str | None) -> None:
    if script_source not in SCRIPT_SOURCES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown script_source '{script_source}'.",
        )
    if script_source == "manual":
        if not script or not script.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A script is required when script_source is 'manual'.",
            )
        limit = pricing.PLAN_SCRIPT_CHAR_LIMIT.get(plan.name, 0)
        if len(script) > limit:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Script exceeds your plan limit of {limit} characters "
                f"(got {len(script)}).",
            )


async def _create_and_reserve_job(
    *,
    db: AsyncSession,
    user,
    plan: Plan,
    channel: YoutubeChannel,
    genre: str,
    duration: str,
    model_requested: str,
    script_source: str,
    script: str | None,
    topic: str | None,
    voice_id: str | None,
    scheduled_for: datetime | None = None,
) -> tuple[VideoJob, int, bool]:
    """Validate, resolve model tier, check affordability, create job, reserve credits.

    Returns (job, credits_charged, fell_back_to_balanced). Raises HTTPException on failure.
    Does not commit — caller is responsible (get_db commits on success).
    """
    _validate_generation_inputs(plan, genre, duration, model_requested)
    _validate_manual_script(plan, script_source, script)

    effective_model, fell_back = await credit_service.resolve_model_tier(
        db, user, plan, model_requested
    )

    credits = pricing.credits_for_video(duration, effective_model)
    if not credit_service.can_afford(user, credits):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "message": "Insufficient credits.",
                "needed": credits,
                "balance": credit_service.balance(user),
                "topup_url": _topup_url(),
            },
        )

    genre_def = genres_mod.get_genre(genre)
    resolved_voice = voice_id or genre_def["default_voice_id"]

    job = VideoJob(
        user_id=user.id,
        channel_id=channel.id,
        genre=genre,
        duration_tier=duration,
        model_tier=effective_model,
        script_source=script_source,
        topic=topic,
        script=script if script_source == "manual" else None,
        voice_id=resolved_voice,
        voice_settings=genre_def["voice_settings"],
        credits_cost=credits,
        scheduled_for=scheduled_for,
        approval_token=secrets.token_urlsafe(32),
        status="queued",
    )
    db.add(job)
    await db.flush()

    await credit_service.reserve_for_video(
        db, user, duration=duration, model=effective_model, job_id=job.id
    )
    await db.refresh(job)
    return job, credits, fell_back


@router.get("/", response_model=VideoListResponse)
async def list_videos(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_filter: str | None = Query(default=None, alias="status"),
    channel_id: UUID | None = Query(default=None),
    genre: str | None = Query(default=None),
    current_user=Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(VideoJob).where(VideoJob.user_id == current_user.id)
    if status_filter:
        stmt = stmt.where(VideoJob.status == status_filter)
    if channel_id:
        stmt = stmt.where(VideoJob.channel_id == channel_id)
    if genre:
        stmt = stmt.where(VideoJob.genre == genre)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    stmt = stmt.order_by(VideoJob.created_at.desc())
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    jobs = result.scalars().all()

    return VideoListResponse(
        items=[VideoJobOut.model_validate(j) for j in jobs],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/generate", response_model=VideoGenerateResponse, status_code=status.HTTP_202_ACCEPTED)
async def generate_video(
    payload: VideoGenerateRequest,
    current_user=Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
):
    plan = await _load_plan(current_user, db)
    channel = await _load_channel(payload.channel_id, current_user.id, db)
    await credit_service.ensure_period(db, current_user, plan)

    genre = payload.genre or channel.genre
    topic = payload.topic or payload.seed

    job, credits_charged, fell_back = await _create_and_reserve_job(
        db=db,
        user=current_user,
        plan=plan,
        channel=channel,
        genre=genre,
        duration=payload.duration_tier,
        model_requested=payload.model_tier,
        script_source=payload.script_source,
        script=payload.script,
        topic=topic,
        voice_id=payload.voice_id,
        scheduled_for=payload.schedule_for,
    )

    _enqueue_generate(job.id)

    return VideoGenerateResponse(
        job=VideoJobOut.model_validate(job),
        credits_charged=credits_charged,
        fell_back_to_balanced=fell_back,
    )


@router.post(
    "/bulk-generate",
    response_model=list[VideoGenerateResponse],
    status_code=status.HTTP_202_ACCEPTED,
)
async def bulk_generate(
    payload: VideoBulkGenerateRequest,
    current_user=Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
):
    plan = await _load_plan(current_user, db)
    channel = await _load_channel(payload.channel_id, current_user.id, db)
    await credit_service.ensure_period(db, current_user, plan)

    items: list[VideoBulkGenerateItem] = payload.items[:10]  # cap at 10 per request
    if not items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No items to generate."
        )

    responses: list[VideoGenerateResponse] = []
    created_jobs: list[UUID] = []
    for item in items:
        genre = item.genre or channel.genre
        topic = item.topic or item.seed
        job, credits_charged, fell_back = await _create_and_reserve_job(
            db=db,
            user=current_user,
            plan=plan,
            channel=channel,
            genre=genre,
            duration=item.duration_tier,
            model_requested=item.model_tier,
            script_source=item.script_source,
            script=item.script,
            topic=topic,
            voice_id=item.voice_id,
        )
        created_jobs.append(job.id)
        responses.append(
            VideoGenerateResponse(
                job=VideoJobOut.model_validate(job),
                credits_charged=credits_charged,
                fell_back_to_balanced=fell_back,
            )
        )

    for job_id in created_jobs:
        _enqueue_generate(job_id)

    return responses


@router.get("/{job_id}", response_model=VideoJobOut)
async def get_video(
    job_id: UUID,
    current_user=Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
):
    job = await _get_job_or_404(job_id, current_user.id, db)
    return VideoJobOut.model_validate(job)


@router.get("/{job_id}/preview")
async def preview_video(
    job_id: UUID,
    current_user=Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
):
    job = await _get_job_or_404(job_id, current_user.id, db)
    if not job.video_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Video not yet generated."
        )
    if not os.path.exists(job.video_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Video file not found on disk."
        )
    return FileResponse(
        path=job.video_path,
        media_type="video/mp4",
        filename=f"preview_{job_id}.mp4",
    )


@router.post("/{job_id}/approve", response_model=VideoJobOut)
async def approve_video(
    job_id: UUID,
    payload: VideoApproveRequest,
    current_user=Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
):
    job = await _get_job_or_404(job_id, current_user.id, db)
    if job.status != "pending_approval":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job is in '{job.status}' state, cannot approve.",
        )

    job.status = "approved"
    job.approved_at = datetime.now(timezone.utc)
    await db.flush()

    _enqueue_upload(job.id)

    await db.refresh(job)
    return VideoJobOut.model_validate(job)


@router.post("/{job_id}/reject", response_model=VideoJobOut)
async def reject_video(
    job_id: UUID,
    payload: VideoApproveRequest,
    current_user=Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
):
    job = await _get_job_or_404(job_id, current_user.id, db)
    if job.status not in ("pending_approval", "approved"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job is in '{job.status}' state, cannot reject.",
        )

    job.status = "rejected"
    job.error_message = payload.note
    # Refund the reserved credits since the video will not be posted.
    if job.credits_cost:
        await credit_service.refund_video(
            db, current_user, credits=job.credits_cost, model=job.model_tier, job_id=job.id
        )
    await db.flush()
    await db.refresh(job)
    return VideoJobOut.model_validate(job)


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_video(
    job_id: UUID,
    current_user=Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
):
    job = await _get_job_or_404(job_id, current_user.id, db)

    if job.video_path and os.path.exists(job.video_path):
        try:
            os.remove(job.video_path)
        except OSError as exc:
            logger.warning("Could not delete video file %s: %s", job.video_path, exc)

    await db.delete(job)
    await db.flush()


@router.get("/approve/{token}", response_model=VideoJobOut)
async def email_approve(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """Email approval link — no auth required. Validates approval_token."""
    result = await db.execute(select(VideoJob).where(VideoJob.approval_token == token))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid approval token.")

    if job.status != "pending_approval":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job is in '{job.status}' state.",
        )

    job.status = "approved"
    job.approved_at = datetime.now(timezone.utc)
    await db.flush()

    _enqueue_upload(job.id)

    await db.refresh(job)
    return VideoJobOut.model_validate(job)
