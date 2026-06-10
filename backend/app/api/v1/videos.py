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

from app.core.config import settings
from app.core.dependencies import get_current_verified_user, get_db
from app.models.channel import YoutubeChannel
from app.models.video_job import VideoJob
from app.schemas.video import (
    VideoApproveRequest,
    VideoBulkGenerateRequest,
    VideoGenerateRequest,
    VideoJobOut,
    VideoListResponse,
)

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


@router.get("/", response_model=VideoListResponse)
async def list_videos(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_filter: str | None = Query(default=None, alias="status"),
    channel_id: UUID | None = Query(default=None),
    current_user=Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(VideoJob).where(VideoJob.user_id == current_user.id)
    if status_filter:
        stmt = stmt.where(VideoJob.status == status_filter)
    if channel_id:
        stmt = stmt.where(VideoJob.channel_id == channel_id)

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


@router.post("/generate", response_model=VideoJobOut, status_code=status.HTTP_202_ACCEPTED)
async def generate_video(
    payload: VideoGenerateRequest,
    current_user=Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
):
    # Verify channel ownership
    ch_result = await db.execute(
        select(YoutubeChannel).where(
            YoutubeChannel.id == payload.channel_id,
            YoutubeChannel.user_id == current_user.id,
            YoutubeChannel.is_active == True,  # noqa: E712
        )
    )
    channel = ch_result.scalar_one_or_none()
    if not channel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found.")

    # Check monthly usage against plan
    from app.models.plan import Plan
    from calendar import monthrange

    now = datetime.now(timezone.utc)
    first_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if current_user.plan_id:
        plan_res = await db.execute(select(Plan).where(Plan.id == current_user.plan_id))
        plan = plan_res.scalar_one_or_none()
        if plan and plan.shorts_per_month is not None:
            used_res = await db.execute(
                select(func.count()).select_from(VideoJob).where(
                    VideoJob.user_id == current_user.id,
                    VideoJob.created_at >= first_of_month,
                )
            )
            used = used_res.scalar_one()
            if used >= plan.shorts_per_month:
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail=f"Monthly limit of {plan.shorts_per_month} shorts reached. Upgrade your plan.",
                )

    job = VideoJob(
        user_id=current_user.id,
        channel_id=payload.channel_id,
        format_slug=payload.format or channel.default_format,
        topic=payload.topic,
        voice_provider=payload.voice_provider or channel.default_voice_provider,
        voice_id=payload.voice_id or channel.default_voice_id,
        scheduled_for=payload.schedule_for,
        approval_token=secrets.token_urlsafe(32),
        status="queued",
    )
    db.add(job)
    await db.flush()
    await db.refresh(job)

    # Queue Celery task
    try:
        from app.workers.celery_app import celery_app

        celery_app.send_task("app.workers.tasks.video_tasks.generate_video", args=[str(job.id)])
    except Exception as exc:
        logger.error("Failed to queue Celery task for job %s: %s", job.id, exc)

    return VideoJobOut.model_validate(job)


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

    # Queue upload task
    try:
        from app.workers.celery_app import celery_app

        celery_app.send_task("app.workers.tasks.video_tasks.upload_to_youtube", args=[str(job.id)])
    except Exception as exc:
        logger.error("Failed to queue upload task for job %s: %s", job.id, exc)

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

    # Remove file if it exists
    if job.video_path and os.path.exists(job.video_path):
        try:
            os.remove(job.video_path)
        except OSError as exc:
            logger.warning("Could not delete video file %s: %s", job.video_path, exc)

    await db.delete(job)
    await db.flush()


@router.post("/bulk-generate", response_model=list[VideoJobOut], status_code=status.HTTP_202_ACCEPTED)
async def bulk_generate(
    payload: VideoBulkGenerateRequest,
    current_user=Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
):
    ch_result = await db.execute(
        select(YoutubeChannel).where(
            YoutubeChannel.id == payload.channel_id,
            YoutubeChannel.user_id == current_user.id,
            YoutubeChannel.is_active == True,  # noqa: E712
        )
    )
    channel = ch_result.scalar_one_or_none()
    if not channel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found.")

    jobs = []
    for i in range(min(payload.count, 10)):  # Cap at 10 per request
        topic = (
            payload.topic_list[i]
            if payload.topic_list and i < len(payload.topic_list)
            else None
        )
        job = VideoJob(
            user_id=current_user.id,
            channel_id=payload.channel_id,
            format_slug=payload.format or channel.default_format,
            topic=topic,
            voice_provider=channel.default_voice_provider,
            voice_id=channel.default_voice_id,
            approval_token=secrets.token_urlsafe(32),
            status="queued",
        )
        db.add(job)
        jobs.append(job)

    await db.flush()
    for job in jobs:
        await db.refresh(job)

    try:
        from app.workers.celery_app import celery_app

        for job in jobs:
            celery_app.send_task("app.workers.tasks.video_tasks.generate_video", args=[str(job.id)])
    except Exception as exc:
        logger.error("Failed to queue bulk tasks: %s", exc)

    return [VideoJobOut.model_validate(j) for j in jobs]


@router.get("/approve/{token}", response_model=VideoJobOut)
async def email_approve(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """Email approval link — no auth required. Validates approval_token."""
    result = await db.execute(
        select(VideoJob).where(VideoJob.approval_token == token)
    )
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

    try:
        from app.workers.celery_app import celery_app

        celery_app.send_task("app.workers.tasks.video_tasks.upload_to_youtube", args=[str(job.id)])
    except Exception as exc:
        logger.error("Failed to queue upload task: %s", exc)

    await db.refresh(job)
    return VideoJobOut.model_validate(job)
