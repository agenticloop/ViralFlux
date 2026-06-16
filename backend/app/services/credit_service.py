"""Credit wallet & metering for ViralFlux.

Two buckets per user:
  - subscription_credits: granted monthly, reset each period (Pro/Agency roll 1 month)
  - topup_credits: bought via packs, never expire while the account is active

Spending draws from subscription first, then top-ups. Every movement is recorded
in the append-only `credit_transactions` ledger. The Max-model quota is tracked on
the user (max_quota_used) and, when exhausted, generation auto-falls back to Balanced.

Final credit-number calibration is deferred (see /pricing.md); all numbers come from
app/core/pricing.py so a final tweak is one line.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import pricing
from app.models.credits import AddonSubscription, CreditTransaction, TopupPurchase
from app.models.plan import Plan
from app.models.user import User


# --------------------------------------------------------------------------- helpers
def _now() -> datetime:
    return datetime.now(timezone.utc)


async def _ledger(
    db: AsyncSession,
    user: User,
    *,
    kind: str,
    amount: int,
    bucket: str,
    job_id=None,
    note: str | None = None,
    extra: dict | None = None,
) -> None:
    db.add(
        CreditTransaction(
            user_id=user.id,
            kind=kind,
            amount=amount,
            balance_after=user.total_credits,
            bucket=bucket,
            job_id=job_id,
            note=note,
            extra=extra,
        )
    )


async def _active_addons(db: AsyncSession, user: User) -> list[str]:
    res = await db.execute(
        select(AddonSubscription.addon).where(
            AddonSubscription.user_id == user.id,
            AddonSubscription.is_active.is_(True),
        )
    )
    return [r[0] for r in res.all()]


# --------------------------------------------------------------------------- granting
async def grant_subscription_credits(db: AsyncSession, user: User, plan: Plan) -> None:
    """Grant a fresh monthly allowance and (re)start the billing period."""
    rollover = 0
    if plan.name in ("pro", "agency") and user.credits_period_end and user.subscription_credits:
        # 1-month rollover for Pro/Agency.
        rollover = user.subscription_credits

    user.subscription_credits = plan.credits_per_month + rollover
    user.max_quota_used = 0
    user.credits_period_start = _now()
    user.credits_period_end = _now() + timedelta(days=30)
    await _ledger(
        db, user,
        kind="subscription_grant",
        amount=plan.credits_per_month,
        bucket="subscription",
        note=f"Monthly grant for plan '{plan.name}'"
        + (f" (+{rollover} rollover)" if rollover else ""),
    )


async def ensure_period(db: AsyncSession, user: User, plan: Plan | None) -> None:
    """Re-grant if the billing period has lapsed. Safe to call on each request."""
    if plan is None:
        return
    if user.credits_period_end is None or user.credits_period_end < _now():
        await grant_subscription_credits(db, user, plan)


# --------------------------------------------------------------------------- balance
def balance(user: User) -> int:
    return user.total_credits


def can_afford(user: User, credits: int) -> bool:
    return user.total_credits >= credits


# --------------------------------------------------------------------------- model tier
async def resolve_model_tier(
    db: AsyncSession, user: User, plan: Plan, requested: str
) -> tuple[str, bool]:
    """Resolve the effective model tier, applying plan gating + Max quota.

    Returns (effective_tier, fell_back_to_balanced).
    """
    allowed = pricing.PLAN_MODELS.get(plan.name, ["Lite"])
    if requested not in allowed:
        # Requested a locked model → clamp to the best allowed.
        requested = allowed[-1]

    if requested != "Max":
        return requested, False

    quota = plan.max_quota
    addons = await _active_addons(db, user)
    quota += 50 * addons.count("max_booster")  # Max Booster add-on: +50 each

    if user.max_quota_used >= quota:
        # Quota exhausted → fall back to Balanced (or best allowed below Max).
        fallback = "Balanced" if "Balanced" in allowed else allowed[-1]
        return fallback, True
    return "Max", False


# --------------------------------------------------------------------------- spend
async def reserve_for_video(
    db: AsyncSession,
    user: User,
    *,
    duration: str,
    model: str,
    job_id=None,
) -> int:
    """Deduct credits for a video up front. Caller must have checked can_afford.

    Draws subscription first, then top-up. Increments Max quota usage when on Max.
    Returns the number of credits spent.
    """
    cost = pricing.credits_for_video(duration, model)

    from_sub = min(user.subscription_credits, cost)
    from_top = cost - from_sub
    user.subscription_credits -= from_sub
    user.topup_credits -= from_top
    if model == "Max":
        user.max_quota_used += 1

    if from_sub:
        await _ledger(
            db, user, kind="video_spend", amount=-from_sub, bucket="subscription",
            job_id=job_id, note=f"{duration} {model} video",
        )
    if from_top:
        await _ledger(
            db, user, kind="video_spend", amount=-from_top, bucket="topup",
            job_id=job_id, note=f"{duration} {model} video",
        )
    return cost


async def refund_video(db: AsyncSession, user: User, *, credits: int, model: str, job_id=None) -> None:
    """Refund a previously-reserved video cost (e.g. generation failed)."""
    user.subscription_credits += credits
    if model == "Max" and user.max_quota_used > 0:
        user.max_quota_used -= 1
    await _ledger(
        db, user, kind="refund", amount=credits, bucket="subscription",
        job_id=job_id, note="Refund: generation failed",
    )


# --------------------------------------------------------------------------- top-ups
async def apply_topup(db: AsyncSession, user: User, pack: str) -> TopupPurchase:
    if pack not in pricing.TOPUP_PACKS:
        raise ValueError(f"Unknown top-up pack '{pack}'")
    credits, price = pricing.TOPUP_PACKS[pack]
    user.topup_credits += credits
    purchase = TopupPurchase(
        user_id=user.id, pack=pack, credits=credits, price_usd=price, status="paid"
    )
    db.add(purchase)
    await _ledger(
        db, user, kind="topup_purchase", amount=credits, bucket="topup",
        note=f"Top-up pack '{pack}' (${price})",
    )
    return purchase


# --------------------------------------------------------------------------- add-ons
async def subscribe_addon(db: AsyncSession, user: User, addon: str) -> AddonSubscription:
    if addon not in pricing.ADDONS:
        raise ValueError(f"Unknown add-on '{addon}'")
    price, _effect, _plans = pricing.ADDONS[addon]
    sub = AddonSubscription(user_id=user.id, addon=addon, price_usd=price, is_active=True)
    db.add(sub)
    return sub
