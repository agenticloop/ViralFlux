"""Integration tests for the /plans API."""
from __future__ import annotations

from app.core import pricing


async def test_list_plans_has_all_four_with_credits(client):
    res = await client.get("/api/v1/plans/")
    assert res.status_code == 200, res.text
    plans = {p["name"]: p for p in res.json()}
    for name in ("free", "starter", "pro", "agency"):
        assert name in plans
        assert plans[name]["credits_per_month"] == pricing.PLAN_CREDITS[name]
    assert plans["free"]["credits_per_month"] == 30


async def test_current_plan_usage_shape(auth, client):
    res = await client.get("/api/v1/plans/current", headers=auth["headers"])
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["plan"]["name"] == "free"
    usage = body["usage"]
    for key in (
        "credits_balance",
        "subscription_credits",
        "topup_credits",
        "credits_per_month",
        "max_quota",
        "max_quota_used",
        "channels_used",
        "channels_limit",
    ):
        assert key in usage
    assert usage["credits_balance"] == 30
    assert usage["channels_used"] == 0
    assert usage["channels_limit"] == 1


async def test_topup_adds_credits(auth, client):
    res = await client.post(
        "/api/v1/plans/topup", json={"pack": "Spark"}, headers=auth["headers"]
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["credits_added"] == 500
    # 30 (free) + 500 topup = 530.
    assert body["credits_balance"] == 530


async def test_topup_unknown_pack_rejected(auth, client):
    res = await client.post(
        "/api/v1/plans/topup", json={"pack": "Bogus"}, headers=auth["headers"]
    )
    assert res.status_code == 400


async def test_upgrade_switches_plan_and_grants_credits(auth, client):
    res = await client.post(
        "/api/v1/plans/upgrade", json={"plan": "pro"}, headers=auth["headers"]
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["plan"]["name"] == "pro"
    # Pro grant = 2600; upgrade resets subscription credits to the new allowance.
    assert body["credits_balance"] == pricing.PLAN_CREDITS["pro"]

    cur = await client.get("/api/v1/plans/current", headers=auth["headers"])
    assert cur.json()["plan"]["name"] == "pro"


async def test_custom_request_inserts_row(client):
    res = await client.post(
        "/api/v1/plans/custom-request",
        json={
            "name": "Big Co",
            "email": "ops@bigco.example.com",
            "channels_needed": 50,
            "videos_per_month": 1000,
        },
    )
    assert res.status_code == 200, res.text
    assert "request_id" in res.json()
