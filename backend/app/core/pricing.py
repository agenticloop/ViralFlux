"""ViralFlux pricing & credit constants.

SINGLE SOURCE OF TRUTH IN CODE — mirrors /pricing.md exactly.
Final credit calibration is deferred until the product works end-to-end and the
client signs off (per plan.md). Every number here is intentionally centralised so
the final tweak is a one-line change.
"""
from __future__ import annotations

# --------------------------------------------------------------- retail / cost
CREDIT_RETAIL_RATE = 0.018            # $/credit at base subscription tier
REAL_COST_PER_CREDIT_WORST = 0.00625  # internal, for margin tracking

# --------------------------------------------------------------- model tiers
MODEL_TIERS = ("Lite", "Balanced", "Max")
MODEL_MULTIPLIER = {"Lite": 0.7, "Balanced": 0.85, "Max": 1.0}

# --------------------------------------------------------------- duration
DURATION_TIERS = ("20s", "30s", "60s", "120s", "150s")

# Base credits priced at the Max model.
VIDEO_CREDITS_BASE = {"20s": 20, "30s": 25, "60s": 40, "120s": 65, "150s": 80}

# Target narration characters per tier (~15 chars/sec) for script trim/pad.
DURATION_CHARS = {"20s": 300, "30s": 450, "60s": 900, "120s": 1800, "150s": 2250}
DURATION_SECONDS = {"20s": 20, "30s": 30, "60s": 60, "120s": 120, "150s": 150}

# --------------------------------------------------------------- plans
PLAN_NAMES = ("free", "starter", "pro", "agency")
PLAN_ORDER = {"free": 0, "starter": 1, "pro": 2, "agency": 3}

PLAN_CREDITS = {"free": 30, "starter": 850, "pro": 2600, "agency": 8000}
MAX_QUOTA = {"free": 0, "starter": 0, "pro": 30, "agency": 120}

# Models a plan may select (UI tiers).
PLAN_MODELS = {
    "free": ["Lite"],
    "starter": ["Lite", "Balanced"],
    "pro": ["Lite", "Balanced", "Max"],
    "agency": ["Lite", "Balanced", "Max"],
}

# Max video duration tier allowed per plan.
PLAN_MAX_DURATION = {"free": "20s", "starter": "60s", "pro": "120s", "agency": "150s"}
PLAN_DURATIONS = {
    "free": ["20s"],
    "starter": ["30s", "60s"],
    "pro": ["30s", "60s", "120s"],
    "agency": ["30s", "60s", "120s", "150s"],
}

PLAN_CHANNELS = {"free": 1, "starter": 2, "pro": 5, "agency": 15}
PLAN_SCRIPT_CHAR_LIMIT = {"free": 300, "starter": 900, "pro": 1800, "agency": 2250}
PLAN_GENRES = {
    "free": ["horror", "brainrot"],          # one locked per channel at free
    "starter": ["horror", "brainrot"],
    "pro": ["horror", "brainrot", "custom"],
    "agency": ["horror", "brainrot", "custom"],
}
PLAN_COMMUNITY_VOICES = {"free": False, "starter": False, "pro": True, "agency": True}
PLAN_TEAM_SEATS = {"free": 1, "starter": 1, "pro": 1, "agency": 3}
PLAN_CREDIT_ROLLOVER = {"free": False, "starter": False, "pro": True, "agency": True}

PLAN_PRICE_MONTHLY = {"free": 0, "starter": 19, "pro": 49, "agency": 129}
PLAN_PRICE_YEARLY = {"free": 0, "starter": 190, "pro": 490, "agency": 1290}

# --------------------------------------------------------------- top-up packs
# name: (credits, price_usd)
TOPUP_PACKS = {
    "Spark": (500, 12),
    "Boost": (1500, 32),
    "Surge": (4000, 78),
    "Blitz": (10000, 180),
}

# --------------------------------------------------------------- add-ons
# name: (price_usd, effect, available_to[plans])
ADDONS = {
    "voice_vault": (9, "community_voices", ["starter"]),
    "max_booster": (15, "max_plus_50", ["pro", "agency"]),
    "extra_channel": (6, "channel_plus_1", ["starter", "pro"]),
    "priority_queue": (12, "priority", ["starter", "pro"]),
}

# --------------------------------------------------------------- voice cost
FLASH_COST_PER_CHAR = 103 / 1_000_000  # $0.000103/char (eleven_flash_v2_5)


def credits_for_video(duration: str, model: str) -> int:
    """Credits a single video costs, given its duration tier and UI model tier."""
    base = VIDEO_CREDITS_BASE[duration]
    return round(base * MODEL_MULTIPLIER[model])


def tts_cost_usd(script: str) -> float:
    """Real ElevenLabs cost for a narration script."""
    return len(script) * FLASH_COST_PER_CHAR


def plan_feature_dict(name: str) -> dict:
    """Build the JSON `features` blob stored on the Plan row for a plan name."""
    return {
        "credits_per_month": PLAN_CREDITS[name],
        "max_quota": MAX_QUOTA[name],
        "models": PLAN_MODELS[name],
        "durations": PLAN_DURATIONS[name],
        "max_duration": PLAN_MAX_DURATION[name],
        "genres": PLAN_GENRES[name],
        "script_char_limit": PLAN_SCRIPT_CHAR_LIMIT[name],
        "community_voices": PLAN_COMMUNITY_VOICES[name],
        "team_seats": PLAN_TEAM_SEATS[name],
        "credit_rollover": PLAN_CREDIT_ROLLOVER[name],
        "price_yearly": PLAN_PRICE_YEARLY[name],
    }
