from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import pricing
from app.core.dependencies import get_current_verified_user, get_db
from app.models.channel import YoutubeChannel
from app.models.credits import CreditTransaction, CustomPlanRequest
from app.models.plan import Plan
from app.schemas.plan import (
    AddonRequest,
    CreditLedgerEntry,
    CurrentPlanOut,
    CustomPlanRequestIn,
    PlanOut,
    TopupRequest,
    UpgradeRequest,
    UsageStats,
)
from app.services import credit_service

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

    # Re-grant credits if the billing period has lapsed.
    await credit_service.ensure_period(db, current_user, plan)

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
            credits_balance=credit_service.balance(current_user),
            subscription_credits=current_user.subscription_credits,
            topup_credits=current_user.topup_credits,
            credits_per_month=plan.credits_per_month,
            max_quota=plan.max_quota,
            max_quota_used=current_user.max_quota_used,
            channels_used=channels_used,
            channels_limit=plan.channels_limit,
            period_start=current_user.credits_period_start,
            period_end=current_user.credits_period_end,
        ),
    )


@router.get("/credits/ledger", response_model=list[CreditLedgerEntry])
async def credits_ledger(
    limit: int = 50,
    current_user=Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
):
    limit = max(1, min(limit, 200))
    result = await db.execute(
        select(CreditTransaction)
        .where(CreditTransaction.user_id == current_user.id)
        .order_by(CreditTransaction.created_at.desc())
        .limit(limit)
    )
    rows = result.scalars().all()
    return [CreditLedgerEntry.model_validate(r) for r in rows]


@router.post("/topup")
async def topup_credits(
    payload: TopupRequest,
    current_user=Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
):
    # Stripe deferred: provision immediately and mark the purchase paid.
    try:
        purchase = await credit_service.apply_topup(db, current_user, payload.pack)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return {
        "message": "Top-up applied.",
        "pack": purchase.pack,
        "credits_added": purchase.credits,
        "price_usd": float(purchase.price_usd),
        "credits_balance": credit_service.balance(current_user),
    }


@router.post("/addons")
async def subscribe_addon(
    payload: AddonRequest,
    current_user=Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
):
    # Stripe deferred: activate the add-on immediately.
    try:
        sub = await credit_service.subscribe_addon(db, current_user, payload.addon)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return {
        "message": "Add-on activated.",
        "addon": sub.addon,
        "price_usd": float(sub.price_usd),
        "is_active": sub.is_active,
    }


@router.post("/custom-request")
async def custom_plan_request(
    payload: CustomPlanRequestIn,
    db: AsyncSession = Depends(get_db),
):
    # Public lead form — no auth required (auth-optional).
    req = CustomPlanRequest(
        name=payload.name,
        email=payload.email,
        channels_needed=payload.channels_needed,
        videos_per_month=payload.videos_per_month,
        max_duration=payload.max_duration,
        team_seats=payload.team_seats,
        genres=payload.genres,
        notes=payload.notes,
        status="pending",
    )
    db.add(req)
    await db.flush()
    return {"message": "Custom plan request submitted.", "request_id": str(req.id)}


@router.post("/upgrade")
async def upgrade_plan(
    payload: UpgradeRequest,
    current_user=Depends(get_current_verified_user),
    db: AsyncSession = Depends(get_db),
):
    # Stripe deferred: switch the plan immediately and grant the new allowance so
    # testing works end-to-end without a payment provider.
    if payload.plan not in pricing.PLAN_NAMES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown plan '{payload.plan}'."
        )

    plan_result = await db.execute(select(Plan).where(Plan.name == payload.plan))
    plan = plan_result.scalar_one_or_none()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Plan '{payload.plan}' not found."
        )

    current_user.plan_id = plan.id
    # Explicit plan switch: do not roll a prior (possibly lower) plan's leftover
    # credits into the new plan's grant.
    await credit_service.grant_subscription_credits(
        db, current_user, plan, allow_rollover=False
    )
    await db.flush()

    return {
        "message": f"Switched to '{plan.name}' plan.",
        "plan": PlanOut.model_validate(plan),
        "credits_balance": credit_service.balance(current_user),
    }
