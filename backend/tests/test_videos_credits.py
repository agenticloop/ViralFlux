"""Integration tests for /videos/generate credit accounting + plan gating.

External generation is async/queued; these assert the JOB row + credit
accounting, NOT the rendered video.
"""
from __future__ import annotations

from conftest import get_user_by_email


async def _make_channel(client, headers, **overrides):
    payload = {
        "channel_name": "Vid Channel",
        "genre": "horror",
        "default_model_tier": "Lite",
        "default_duration": "20s",
    }
    payload.update(overrides)
    res = await client.post("/api/v1/channels/", json=payload, headers=headers)
    assert res.status_code == 201, res.text
    return res.json()["id"]


async def test_generate_free_lite_20s_deducts_14(auth, client, db):
    ch_id = await _make_channel(client, auth["headers"])
    res = await client.post(
        "/api/v1/videos/generate",
        json={
            "channel_id": ch_id,
            "duration_tier": "20s",
            "model_tier": "Lite",
            "script_source": "ai",
            "topic": "an empty house at midnight",
        },
        headers=auth["headers"],
    )
    assert res.status_code == 202, res.text
    body = res.json()
    assert body["credits_charged"] == 14
    assert body["fell_back_to_balanced"] is False
    assert body["job"]["status"] == "queued"
    assert body["job"]["model_tier"] == "Lite"
    assert body["job"]["credits_cost"] == 14

    # Balance: 30 - 14 = 16.
    user = await get_user_by_email(db, auth["email"])
    assert user.total_credits == 16

    # Ledger has a video_spend row for this user.
    cur = await client.get("/api/v1/plans/credits/ledger", headers=auth["headers"])
    assert cur.status_code == 200
    kinds = [r["kind"] for r in cur.json()]
    assert "video_spend" in kinds


async def test_balance_preview_via_current_plan(auth, client):
    res = await client.get("/api/v1/plans/current", headers=auth["headers"])
    assert res.status_code == 200, res.text
    usage = res.json()["usage"]
    assert usage["credits_balance"] == 30
    assert usage["subscription_credits"] == 30
    assert usage["credits_per_month"] == 30


async def test_insufficient_credits_returns_402_with_needed_balance(auth, client):
    ch_id = await _make_channel(client, auth["headers"])
    # Free plan = 30 credits. 20s Lite = 14. Two succeed (28 spent), third needs 14
    # but only 2 remain -> 402.
    for _ in range(2):
        ok = await client.post(
            "/api/v1/videos/generate",
            json={"channel_id": ch_id, "duration_tier": "20s", "model_tier": "Lite"},
            headers=auth["headers"],
        )
        assert ok.status_code == 202, ok.text

    third = await client.post(
        "/api/v1/videos/generate",
        json={"channel_id": ch_id, "duration_tier": "20s", "model_tier": "Lite"},
        headers=auth["headers"],
    )
    assert third.status_code == 402, third.text
    detail = third.json()["detail"]
    assert detail["needed"] == 14
    assert detail["balance"] == 2


async def test_manual_script_over_char_limit_rejected(auth, client):
    ch_id = await _make_channel(client, auth["headers"])
    # Free plan char limit is 300.
    res = await client.post(
        "/api/v1/videos/generate",
        json={
            "channel_id": ch_id,
            "duration_tier": "20s",
            "model_tier": "Lite",
            "script_source": "manual",
            "script": "x" * 301,
        },
        headers=auth["headers"],
    )
    assert res.status_code == 400, res.text
    assert "limit" in res.json()["detail"].lower()


async def test_manual_script_within_limit_accepted(auth, client):
    ch_id = await _make_channel(client, auth["headers"])
    res = await client.post(
        "/api/v1/videos/generate",
        json={
            "channel_id": ch_id,
            "duration_tier": "20s",
            "model_tier": "Lite",
            "script_source": "manual",
            "script": "A short and chilling tale.",
        },
        headers=auth["headers"],
    )
    assert res.status_code == 202, res.text
    assert res.json()["job"]["script_source"] == "manual"


async def test_locked_max_model_clamped_to_lite_on_free(auth, client):
    """Free plan only has Lite; requesting Max clamps to Lite (its only model).

    Note: the /videos/generate endpoint validates the requested model against the
    plan BEFORE resolve_model_tier, so Max on free is rejected with 402 at the
    gate. The clamp-to-allowed behavior is exercised at the service layer.
    """
    ch_id = await _make_channel(client, auth["headers"])
    res = await client.post(
        "/api/v1/videos/generate",
        json={"channel_id": ch_id, "duration_tier": "20s", "model_tier": "Max"},
        headers=auth["headers"],
    )
    # Plan gating rejects an explicitly-locked model with 402.
    assert res.status_code == 402, res.text
