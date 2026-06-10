from __future__ import annotations

import logging
from datetime import timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.dependencies import get_current_verified_user, get_db
from app.core.security import decrypt_token, encrypt_token
from app.models.analytics import VideoAnalytic
from app.models.channel import ChannelSchedule, YoutubeChannel
from app.models.plan import Plan
from app.models.video_job import VideoJob
from app.schemas.channel import (
    ChannelCreate,
    ChannelOut,
    ChannelUpdate,
    ScheduleConfig,
    ScheduleOut,
)
from app.services.postproxy_service import PostProxyError, PostProxyService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/channels", tags=["channels"])


async def _get_channel_or_404(
    channel_id: UUID,
    user_id: UUID,
    db: AsyncSession,
    *,
    load_schedule: bool = False,
) -> YoutubeChannel:
    stmt = select(YoutubeChannel).where(
        YoutubeChannel.id == channel_id,
        YoutubeChannel.user_id == user_id,
        YoutubeChannel.is_active == True,  # noqa: E712
    )
    if load_schedule:
        stmt = stmt.options(selectinload(YoutubeChannel.schedule))
    result = await db.execute(stmt)
    channel = result.scalar_one_or_none()
    if not channel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found.")
    return channel


@router.get("/", response_model=list[ChannelOut])
async def list_channels(
    current_user=Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(YoutubeChannel)
        .where(YoutubeChannel.user_id == current_user.id, YoutubeChannel.is_active == True)  # noqa: E712
        .options(selectinload(YoutubeChannel.schedule))
        .order_by(YoutubeChannel.created_at.desc())
    )
    channels = result.scalars().all()
    return [ChannelOut.model_validate(c) for c in channels]


@router.post("/", response_model=ChannelOut, status_code=status.HTTP_201_CREATED)
async def create_channel(
    payload: ChannelCreate,
    current_user=Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
):
    # Check plan channel limit
    if current_user.plan_id:
        plan_result = await db.execute(select(Plan).where(Plan.id == current_user.plan_id))
        plan = plan_result.scalar_one_or_none()
        if plan and plan.channels_limit is not None:
            count_result = await db.execute(
                select(func.count()).select_from(YoutubeChannel).where(
                    YoutubeChannel.user_id == current_user.id,
                    YoutubeChannel.is_active == True,  # noqa: E712
                )
            )
            current_count = count_result.scalar_one()
            if current_count >= plan.channels_limit:
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail=f"Channel limit ({plan.channels_limit}) reached. Upgrade your plan.",
                )

    channel = YoutubeChannel(
        user_id=current_user.id,
        **payload.model_dump(),
    )
    db.add(channel)
    await db.flush()
    await db.refresh(channel)
    return ChannelOut.model_validate(channel)


@router.get("/{channel_id}", response_model=ChannelOut)
async def get_channel(
    channel_id: UUID,
    current_user=Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
):
    channel = await _get_channel_or_404(channel_id, current_user.id, db, load_schedule=True)
    return ChannelOut.model_validate(channel)


@router.put("/{channel_id}", response_model=ChannelOut)
async def update_channel(
    channel_id: UUID,
    payload: ChannelUpdate,
    current_user=Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
):
    channel = await _get_channel_or_404(channel_id, current_user.id, db)
    update_data = payload.model_dump(exclude_none=True)
    for key, value in update_data.items():
        setattr(channel, key, value)
    await db.flush()
    await db.refresh(channel)
    return ChannelOut.model_validate(channel)


@router.delete("/{channel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_channel(
    channel_id: UUID,
    current_user=Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
):
    channel = await _get_channel_or_404(channel_id, current_user.id, db)
    channel.is_active = False  # Soft delete
    await db.flush()


@router.post("/{channel_id}/connect-youtube")
async def connect_youtube(
    channel_id: UUID,
    current_user=Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
):
    """Return a PostProxy OAuth URL for connecting a YouTube channel.

    The user is redirected to Google via PostProxy. After granting access,
    PostProxy redirects back to the frontend which should call
    POST /{channel_id}/link-postproxy with the resulting profile_id.
    """
    await _get_channel_or_404(channel_id, current_user.id, db)

    if not settings.POSTPROXY_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="POSTPROXY_API_KEY is not configured.",
        )

    svc = PostProxyService()
    try:
        groups = await svc.list_profile_groups()
    except PostProxyError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    if not groups:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No PostProxy profile groups found. Create one in the PostProxy dashboard.",
        )

    profile_group_id = groups[0].get("id") or groups[0].get("profile_group_id")
    redirect_url = f"{settings.APP_URL}/dashboard/channels/{channel_id}/postproxy-callback"

    try:
        result = await svc.initialize_connection(profile_group_id, redirect_url)
    except PostProxyError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    return {
        "oauth_url": result.get("url"),
        "connection_id": result.get("connection_id"),
        "profile_group_id": profile_group_id,
    }


@router.post("/{channel_id}/link-postproxy")
async def link_postproxy_profile(
    channel_id: UUID,
    payload: dict,
    current_user=Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
):
    """Store a PostProxy profile_id on this channel.

    Call this after the user completes the PostProxy OAuth flow.
    Body: {"profile_id": "<postproxy-profile-id>"}
    """
    channel = await _get_channel_or_404(channel_id, current_user.id, db)

    profile_id = payload.get("profile_id", "").strip()
    if not profile_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="profile_id is required.",
        )

    channel.postproxy_profile_id = profile_id
    await db.flush()
    return {"message": "PostProxy profile linked.", "profile_id": profile_id}


@router.get("/postproxy-profiles")
async def list_postproxy_profiles(
    current_user=Depends(get_current_verified_user),
):
    """List YouTube profiles connected to PostProxy on this account.

    Use the returned profile IDs with POST /{channel_id}/link-postproxy.
    """
    if not settings.POSTPROXY_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="POSTPROXY_API_KEY is not configured.",
        )

    svc = PostProxyService()
    try:
        profiles = await svc.list_profiles(platform="youtube")
    except PostProxyError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    return {"profiles": profiles}


@router.post("/{channel_id}/schedule", response_model=ScheduleOut)
async def upsert_schedule(
    channel_id: UUID,
    payload: ScheduleConfig,
    current_user=Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_channel_or_404(channel_id, current_user.id, db)

    result = await db.execute(
        select(ChannelSchedule).where(ChannelSchedule.channel_id == channel_id)
    )
    schedule = result.scalar_one_or_none()

    if schedule:
        for key, value in payload.model_dump().items():
            setattr(schedule, key, value)
    else:
        schedule = ChannelSchedule(channel_id=channel_id, **payload.model_dump())
        db.add(schedule)

    await db.flush()
    await db.refresh(schedule)
    return ScheduleOut.model_validate(schedule)


@router.get("/{channel_id}/analytics")
async def channel_analytics(
    channel_id: UUID,
    current_user=Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_channel_or_404(channel_id, current_user.id, db)

    # Total jobs and posted counts
    jobs_result = await db.execute(
        select(func.count()).select_from(VideoJob).where(
            VideoJob.channel_id == channel_id
        )
    )
    total_jobs = jobs_result.scalar_one()

    posted_result = await db.execute(
        select(func.count()).select_from(VideoJob).where(
            VideoJob.channel_id == channel_id,
            VideoJob.status == "posted",
        )
    )
    total_posted = posted_result.scalar_one()

    # Aggregate analytics
    analytics_result = await db.execute(
        select(
            func.sum(VideoAnalytic.views).label("total_views"),
            func.sum(VideoAnalytic.likes).label("total_likes"),
            func.avg(VideoAnalytic.views).label("avg_views"),
        )
        .join(VideoJob, VideoAnalytic.job_id == VideoJob.id)
        .where(VideoJob.channel_id == channel_id)
    )
    row = analytics_result.one()

    return {
        "channel_id": str(channel_id),
        "total_jobs": total_jobs,
        "total_posted": total_posted,
        "total_views": int(row.total_views or 0),
        "total_likes": int(row.total_likes or 0),
        "avg_views_per_video": float(row.avg_views or 0),
    }
