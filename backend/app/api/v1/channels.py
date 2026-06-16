from __future__ import annotations

import logging
import secrets
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core import genres, pricing
from app.core.config import settings
from app.core.dependencies import get_current_verified_user, get_db
from app.core.security import encrypt_token
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
from app.services.tts.voice_catalog import recommended_voices
from app.services.youtube_service import youtube_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/channels", tags=["channels"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


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


async def _load_user_plan(current_user, db: AsyncSession) -> Plan | None:
    if not current_user.plan_id:
        return None
    result = await db.execute(select(Plan).where(Plan.id == current_user.plan_id))
    return result.scalar_one_or_none()


def _plan_name(plan: Plan | None) -> str:
    return plan.name if plan is not None else "free"


def _validate_genre(plan_name: str, genre: str) -> None:
    if genre not in genres.GENRE_SLUGS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown genre '{genre}'.",
        )
    allowed = pricing.PLAN_GENRES.get(plan_name, [])
    if genre not in allowed:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Genre '{genre}' is not available on the '{plan_name}' plan.",
        )


def _validate_model_tier(plan_name: str, tier: str) -> None:
    allowed = pricing.PLAN_MODELS.get(plan_name, [])
    if tier not in allowed:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Model tier '{tier}' is not available on the '{plan_name}' plan.",
        )


def _validate_duration(plan_name: str, duration: str) -> None:
    allowed = pricing.PLAN_DURATIONS.get(plan_name, [])
    if duration not in allowed:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Duration '{duration}' is not available on the '{plan_name}' plan.",
        )


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


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
    plan = await _load_user_plan(current_user, db)
    plan_name = _plan_name(plan)

    # Plan validation: genre / model tier / duration must be allowed.
    _validate_genre(plan_name, payload.genre)
    _validate_model_tier(plan_name, payload.default_model_tier)
    _validate_duration(plan_name, payload.default_duration)

    # Enforce per-plan channel limit.
    channels_limit = pricing.PLAN_CHANNELS.get(plan_name)
    if plan is not None and plan.channels_limit is not None:
        channels_limit = plan.channels_limit
    if channels_limit is not None:
        count_result = await db.execute(
            select(func.count()).select_from(YoutubeChannel).where(
                YoutubeChannel.user_id == current_user.id,
                YoutubeChannel.is_active == True,  # noqa: E712
            )
        )
        current_count = count_result.scalar_one()
        if current_count >= channels_limit:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"Channel limit ({channels_limit}) reached. Upgrade your plan.",
            )

    genre_cfg = genres.get_genre(payload.genre)
    music_bucket = payload.music_bucket or genre_cfg["music_bucket"]
    voice_id = payload.voice_id or genre_cfg["default_voice_id"]

    channel = YoutubeChannel(
        user_id=current_user.id,
        channel_name=payload.channel_name,
        genre=payload.genre,
        seed_prompt=payload.seed_prompt,
        seed_prompt_updated_at=datetime.utcnow() if payload.seed_prompt else None,
        default_model_tier=payload.default_model_tier,
        default_duration=payload.default_duration,
        voice_id=voice_id,
        voice_name=payload.voice_name,
        music_bucket=music_bucket,
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
    plan = await _load_user_plan(current_user, db)
    plan_name = _plan_name(plan)

    update_data = payload.model_dump(exclude_unset=True)

    if "genre" in update_data and update_data["genre"] is not None:
        _validate_genre(plan_name, update_data["genre"])
    if (
        "default_model_tier" in update_data
        and update_data["default_model_tier"] is not None
    ):
        _validate_model_tier(plan_name, update_data["default_model_tier"])
    if (
        "default_duration" in update_data
        and update_data["default_duration"] is not None
    ):
        _validate_duration(plan_name, update_data["default_duration"])

    for key, value in update_data.items():
        if value is None:
            continue
        setattr(channel, key, value)
        if key == "seed_prompt":
            channel.seed_prompt_updated_at = datetime.utcnow()

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


# ---------------------------------------------------------------------------
# YouTube OAuth (direct, multi-account)
# ---------------------------------------------------------------------------


@router.post("/{channel_id}/connect-youtube")
async def connect_youtube(
    channel_id: UUID,
    current_user=Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
):
    """Begin the direct Google OAuth flow for connecting this channel.

    Generates a random ``state``, stores it on the channel row, and returns the
    Google consent-screen URL. After the user grants access Google redirects to
    ``GET /channels/youtube/callback``.
    """
    channel = await _get_channel_or_404(channel_id, current_user.id, db)

    state = secrets.token_urlsafe(32)
    channel.oauth_state = state
    await db.flush()

    try:
        auth_url = youtube_service.get_auth_url(str(channel_id), state)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )
    return {"auth_url": auth_url}


@router.get("/youtube/callback")
async def youtube_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """OAuth redirect target hit by Google (no auth dependency).

    The originating channel is resolved via the opaque ``state`` we stored on
    the row in ``connect-youtube``. Tokens + channel info are persisted
    (tokens encrypted) and the user is redirected back to the dashboard.
    """
    result = await db.execute(
        select(YoutubeChannel).where(
            YoutubeChannel.oauth_state == state,
            YoutubeChannel.is_active == True,  # noqa: E712
        )
    )
    channel = result.scalar_one_or_none()
    if not channel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired OAuth state.",
        )

    try:
        tokens = await youtube_service.exchange_code(code)
    except Exception as exc:  # noqa: BLE001 - surface a clean error to caller
        logger.warning("YouTube OAuth code exchange failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to connect YouTube channel: {exc}",
        )

    channel.youtube_channel_id = tokens.get("channel_id") or None
    channel.youtube_channel_title = tokens.get("channel_title") or None
    channel.youtube_thumbnail_url = tokens.get("thumbnail_url") or None
    channel.google_account_email = tokens.get("email") or None

    access_token = tokens.get("access_token") or ""
    refresh_token = tokens.get("refresh_token") or ""
    channel.oauth_access_token = encrypt_token(access_token) if access_token else None
    channel.oauth_refresh_token = encrypt_token(refresh_token) if refresh_token else None

    expiry_str = tokens.get("expiry") or ""
    if expiry_str:
        try:
            channel.oauth_expiry = datetime.fromisoformat(expiry_str)
        except ValueError:
            channel.oauth_expiry = None
    else:
        channel.oauth_expiry = None

    channel.oauth_state = None
    await db.flush()

    redirect_url = (
        f"{settings.FRONTEND_URL}/dashboard/channels/{channel.id}?connected=1"
    )
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)


@router.post("/{channel_id}/disconnect-youtube")
async def disconnect_youtube(
    channel_id: UUID,
    current_user=Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
):
    """Clear all stored OAuth tokens + connected-account info for a channel."""
    channel = await _get_channel_or_404(channel_id, current_user.id, db)

    channel.oauth_access_token = None
    channel.oauth_refresh_token = None
    channel.oauth_expiry = None
    channel.oauth_state = None
    channel.google_account_email = None
    channel.youtube_channel_id = None
    channel.youtube_channel_title = None
    channel.youtube_thumbnail_url = None
    await db.flush()
    return {"message": "YouTube channel disconnected."}


# ---------------------------------------------------------------------------
# Schedule / voices / analytics
# ---------------------------------------------------------------------------


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

    data = payload.model_dump()
    if schedule:
        for key, value in data.items():
            setattr(schedule, key, value)
    else:
        schedule = ChannelSchedule(channel_id=channel_id, **data)
        db.add(schedule)

    await db.flush()
    await db.refresh(schedule)
    return ScheduleOut.model_validate(schedule)


@router.get("/{channel_id}/voices")
async def channel_voices(
    channel_id: UUID,
    current_user=Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
):
    channel = await _get_channel_or_404(channel_id, current_user.id, db)
    return {"voices": recommended_voices(channel.genre)}


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
