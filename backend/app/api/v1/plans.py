from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_verified_user, get_db
from app.models.channel import YoutubeChannel
from app.models.plan import Plan
from app.models.video_job import VideoJob
from app.schemas.plan import CurrentPlanOut, PlanOut, UsageStats

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/plans", tags=["plans"])


@router.get("/", response_model=list[PlanOut])
async def list_plans(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Plan).order_by(Plan.price_usd))
    plans = result.scalars().all()
    return [PlanOut.model_validate(p) for p in plans]


@router.get("/current", response_model=CurrentPlanOut)
async def current_plan(
    current_user=Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.plan_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No plan assigned to user."
        )

    plan_result = await db.execute(select(Plan).where(Plan.id == current_user.plan_id))
    plan = plan_result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found.")

    now = datetime.now(timezone.utc)
    first_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Shorts used this month
    shorts_result = await db.execute(
        select(func.count()).select_from(VideoJob).where(
            VideoJob.user_id == current_user.id,
            VideoJob.created_at >= first_of_month,
        )
    )
    shorts_used = shorts_result.scalar_one()

    # Channels used
    channels_result = await db.execute(
        select(func.count()).select_from(YoutubeChannel).where(
            YoutubeChannel.user_id == current_user.id,
            YoutubeChannel.is_active == True,  # noqa: E712
        )
    )
    channels_used = channels_result.scalar_one()

    return CurrentPlanOut(
        plan=PlanOut.model_validate(plan),
        usage=UsageStats(
            shorts_used=shorts_used,
            shorts_limit=plan.shorts_per_month,
            channels_used=channels_used,
            channels_limit=plan.channels_limit,
        ),
    )


@router.post("/upgrade")
async def upgrade_plan(current_user=Depends(get_current_verified_user)):
    return {"message": "Stripe integration coming soon. Contact support@viralflux.io to upgrade."}
