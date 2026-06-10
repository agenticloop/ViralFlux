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
from app.schemas.channel import ChannelCreate, ChannelOut, ChannelUpdate, ScheduleConfig, ScheduleOut

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
    """Return the Google OAuth URL for connecting a YouTube channel."""
    await _get_channel_or_404(channel_id, current_user.id, db)

    from google_auth_oauthlib.flow import Flow

    scopes = [
        "https://www.googleapis.com/auth/youtube.upload",
        "https://www.googleapis.com/auth/youtube.readonly",
    ]
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": settings.YOUTUBE_CLIENT_ID,
                "client_secret": settings.YOUTUBE_CLIENT_SECRET,
                "redirect_uris": [settings.YOUTUBE_REDIRECT_URI],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=scopes,
        redirect_uri=settings.YOUTUBE_REDIRECT_URI,
    )
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        state=str(channel_id),
        prompt="consent",
    )
    return {"oauth_url": auth_url}


@router.get("/{channel_id}/oauth-callback")
async def oauth_callback(
    channel_id: UUID,
    code: str,
    current_user=Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
):
    """Handle YouTube OAuth callback, store encrypted tokens."""
    channel = await _get_channel_or_404(channel_id, current_user.id, db)

    from datetime import datetime

    from google_auth_oauthlib.flow import Flow

    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": settings.YOUTUBE_CLIENT_ID,
                "client_secret": settings.YOUTUBE_CLIENT_SECRET,
                "redirect_uris": [settings.YOUTUBE_REDIRECT_URI],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=[
            "https://www.googleapis.com/auth/youtube.upload",
            "https://www.googleapis.com/auth/youtube.readonly",
        ],
        redirect_uri=settings.YOUTUBE_REDIRECT_URI,
    )
    flow.fetch_token(code=code)
    credentials = flow.credentials

    channel.oauth_access_token = encrypt_token(credentials.token)
    channel.oauth_refresh_token = (
        encrypt_token(credentials.refresh_token) if credentials.refresh_token else None
    )
    channel.oauth_expiry = credentials.expiry

    # Fetch YouTube channel ID
    try:
        from googleapiclient.discovery import build

        youtube = build("youtube", "v3", credentials=credentials)
        resp = youtube.channels().list(part="id", mine=True).execute()
        items = resp.get("items", [])
        if items:
            channel.youtube_channel_id = items[0]["id"]
    except Exception as exc:
        logger.warning("Could not fetch YouTube channel ID: %s", exc)

    await db.flush()
    return {"message": "YouTube channel connected successfully.", "channel_id": str(channel_id)}


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
