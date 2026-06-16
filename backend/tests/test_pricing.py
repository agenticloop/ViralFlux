"""Pure unit tests for app.core.pricing — no DB, no app."""
from __future__ import annotations

import pytest

from app.core import pricing


@pytest.mark.parametrize("duration", pricing.DURATION_TIERS)
@pytest.mark.parametrize("model", pricing.MODEL_TIERS)
def test_credits_for_video_matches_multiplier_math(duration, model):
    expected = round(pricing.VIDEO_CREDITS_BASE[duration] * pricing.MODEL_MULTIPLIER[model])
    assert pricing.credits_for_video(duration, model) == expected


def test_max_model_equals_base():
    # Max multiplier is 1.0, so Max credits == base.
    for d in pricing.DURATION_TIERS:
        assert pricing.credits_for_video(d, "Max") == pricing.VIDEO_CREDITS_BASE[d]


def test_lite_is_cheapest_balanced_middle():
    for d in pricing.DURATION_TIERS:
        lite = pricing.credits_for_video(d, "Lite")
        bal = pricing.credits_for_video(d, "Balanced")
        mx = pricing.credits_for_video(d, "Max")
        assert lite <= bal <= mx


def test_plan_feature_dict_shape():
    expected_keys = {
        "credits_per_month",
        "max_quota",
        "models",
        "durations",
        "max_duration",
        "genres",
        "script_char_limit",
        "community_voices",
        "team_seats",
        "credit_rollover",
        "price_yearly",
    }
    for name in pricing.PLAN_NAMES:
        d = pricing.plan_feature_dict(name)
        assert set(d.keys()) == expected_keys
        assert d["credits_per_month"] == pricing.PLAN_CREDITS[name]
        assert d["max_quota"] == pricing.MAX_QUOTA[name]
        assert d["models"] == pricing.PLAN_MODELS[name]
        assert d["script_char_limit"] == pricing.PLAN_SCRIPT_CHAR_LIMIT[name]


def test_free_plan_constants():
    assert pricing.PLAN_CREDITS["free"] == 30
    assert pricing.PLAN_MODELS["free"] == ["Lite"]
    assert pricing.PLAN_CHANNELS["free"] == 1
    assert pricing.MAX_QUOTA["free"] == 0


def test_topup_pack_table():
    assert pricing.TOPUP_PACKS["Spark"] == (500, 12)
    assert pricing.TOPUP_PACKS["Boost"] == (1500, 32)
    assert pricing.TOPUP_PACKS["Surge"] == (4000, 78)
    assert pricing.TOPUP_PACKS["Blitz"] == (10000, 180)
    # Credits monotonically increase with price.
    ordered = sorted(pricing.TOPUP_PACKS.values(), key=lambda v: v[1])
    credits = [c for c, _ in ordered]
    assert credits == sorted(credits)


def test_addon_table_effects_and_availability():
    assert pricing.ADDONS["max_booster"][1] == "max_plus_50"
    assert "pro" in pricing.ADDONS["max_booster"][2]
    assert "agency" in pricing.ADDONS["max_booster"][2]
    assert pricing.ADDONS["voice_vault"][1] == "community_voices"
    assert pricing.ADDONS["extra_channel"][1] == "channel_plus_1"


def test_lite_20s_credits_is_14():
    # round(20 * 0.7) == 14 — the canonical free-plan video cost.
    assert pricing.credits_for_video("20s", "Lite") == 14
