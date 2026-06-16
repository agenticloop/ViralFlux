"""Unit tests for app.services.credit_service against the test DB."""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select

from app.core import pricing
from app.models.credits import AddonSubscription, CreditTransaction, TopupPurchase
from app.models.plan import Plan
from app.models.user import User
from app.services import credit_service

from conftest import get_plan_by_name


async def _make_user(db, email_prefix="cs") -> User:
    u = User(
        email=f"{email_prefix}-{uuid.uuid4().hex[:10]}@example.com",
        password_hash="x",
        is_verified=True,
    )
    db.add(u)
    await db.flush()
    return u


async def test_grant_free_plan_is_30(db):
    free = await get_plan_by_name(db, "free")
    u = await _make_user(db)
    await credit_service.grant_subscription_credits(db, u, free)
    assert u.subscription_credits == 30
    assert u.total_credits == 30
    # A ledger row was created for the grant.
    res = await db.execute(
        select(CreditTransaction).where(
            CreditTransaction.user_id == u.id,
            CreditTransaction.kind == "subscription_grant",
        )
    )
    rows = res.scalars().all()
    assert len(rows) == 1
    assert rows[0].amount == 30


async def test_reserve_draws_subscription_then_topup(db):
    u = await _make_user(db)
    u.subscription_credits = 10
    u.topup_credits = 100
    await db.flush()

    # 20s Lite = round(20*0.7) = 14. Sub has 10 → 10 from sub, 4 from topup.
    cost = await credit_service.reserve_for_video(db, u, duration="20s", model="Lite")
    assert cost == 14
    assert u.subscription_credits == 0
    assert u.topup_credits == 96

    res = await db.execute(
        select(CreditTransaction).where(
            CreditTransaction.user_id == u.id,
            CreditTransaction.kind == "video_spend",
        )
    )
    txs = res.scalars().all()
    buckets = {t.bucket: t.amount for t in txs}
    assert buckets["subscription"] == -10
    assert buckets["topup"] == -4


async def test_refund_restores_subscription(db):
    u = await _make_user(db)
    u.subscription_credits = 50
    await db.flush()
    cost = await credit_service.reserve_for_video(db, u, duration="20s", model="Lite")
    assert u.subscription_credits == 50 - cost
    await credit_service.refund_video(db, u, credits=cost, model="Lite")
    assert u.subscription_credits == 50


async def test_resolve_model_clamps_locked_model_to_plan(db):
    """Free plan only allows Lite — requesting Max clamps down to Lite."""
    free = await get_plan_by_name(db, "free")
    u = await _make_user(db)
    effective, fell_back = await credit_service.resolve_model_tier(db, u, free, "Max")
    assert effective == "Lite"
    # Not "fell_back_to_balanced" — it was clamped, never reached Max path.
    assert fell_back is False


async def test_resolve_model_max_quota_fallback(db):
    """Pro plan allows Max but with quota=30; once exhausted -> Balanced fallback."""
    pro = await get_plan_by_name(db, "pro")
    u = await _make_user(db)
    # Within quota: Max stays Max.
    eff, fb = await credit_service.resolve_model_tier(db, u, pro, "Max")
    assert eff == "Max"
    assert fb is False
    # Exhaust the quota.
    u.max_quota_used = pro.max_quota
    await db.flush()
    eff, fb = await credit_service.resolve_model_tier(db, u, pro, "Max")
    assert eff == "Balanced"
    assert fb is True


async def test_max_booster_addon_adds_50(db):
    pro = await get_plan_by_name(db, "pro")
    u = await _make_user(db)
    # At exactly base quota, Max would fall back...
    u.max_quota_used = pro.max_quota
    await db.flush()
    eff, fb = await credit_service.resolve_model_tier(db, u, pro, "Max")
    assert eff == "Balanced" and fb is True
    # ...but with max_booster (+50) the effective quota is base+50, so Max is back.
    db.add(AddonSubscription(user_id=u.id, addon="max_booster", price_usd=15, is_active=True))
    await db.flush()
    eff, fb = await credit_service.resolve_model_tier(db, u, pro, "Max")
    assert eff == "Max"
    assert fb is False


async def test_apply_topup_adds_credits_and_ledger(db):
    u = await _make_user(db)
    before = u.topup_credits
    purchase = await credit_service.apply_topup(db, u, "Boost")
    credits, price = pricing.TOPUP_PACKS["Boost"]
    assert u.topup_credits == before + credits
    assert isinstance(purchase, TopupPurchase)
    assert purchase.credits == credits
    assert purchase.status == "paid"

    res = await db.execute(
        select(CreditTransaction).where(
            CreditTransaction.user_id == u.id,
            CreditTransaction.kind == "topup_purchase",
        )
    )
    rows = res.scalars().all()
    assert len(rows) == 1
    assert rows[0].amount == credits
    assert rows[0].bucket == "topup"


async def test_apply_topup_unknown_pack_raises(db):
    u = await _make_user(db)
    with pytest.raises(ValueError):
        await credit_service.apply_topup(db, u, "Nope")


async def test_renewal_rollover_vs_upgrade_no_rollover(db):
    """Pro/Agency renewal rolls leftover credits; an explicit switch does not."""
    pro = await get_plan_by_name(db, "pro")
    u = await _make_user(db)
    # Simulate an active pro user mid-period with leftover credits.
    await credit_service.grant_subscription_credits(db, u, pro)
    u.subscription_credits = 100  # leftover from the period
    await db.flush()

    # Renewal of the SAME pro plan rolls the 100 over: 2600 + 100.
    await credit_service.grant_subscription_credits(db, u, pro)
    assert u.subscription_credits == pricing.PLAN_CREDITS["pro"] + 100

    # An explicit plan switch must NOT roll over (allow_rollover=False).
    u.subscription_credits = 100
    await db.flush()
    await credit_service.grant_subscription_credits(db, u, pro, allow_rollover=False)
    assert u.subscription_credits == pricing.PLAN_CREDITS["pro"]


async def test_reserve_increments_max_quota(db):
    pro = await get_plan_by_name(db, "pro")
    u = await _make_user(db)
    u.subscription_credits = 1000
    await db.flush()
    assert u.max_quota_used == 0
    await credit_service.reserve_for_video(db, u, duration="60s", model="Max")
    assert u.max_quota_used == 1
