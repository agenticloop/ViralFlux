# ViralFlux — Pricing & Credits (Single Source of Truth)

> This file is the **authoritative** spec for plans, the AI credit system, model tiers,
> add-ons, top-ups, and unit economics. The backend `pricing` constants module is
> generated to match this file exactly. **Recalculate every table whenever an API rate
> or the model stack changes.**
>
> Status: **credit numbers are LIVE in code but the FINAL calibration is deferred** until
> the full product works end-to-end and the client signs off (per plan.md). All constants
> live in ONE place (`backend/app/core/pricing.py`) so a final tweak is a one-line change.

---

## 1. Core Principle

Users never see tokens, characters, or API costs. They see **credits** and **videos**.
Every credit maps to a fixed, known real cost.

- **1 credit ≈ $0.018 retail value** (base subscription tier)
- **Real cost backing 1 credit ≈ $0.00625** (worst case, Max model)
- **Baked-in blended margin: 60–74%** across every plan, pack, and add-on

The LLM tier barely affects real cost (LLM is <$0.01/video). Real cost is **images + voice**,
both driven by **video duration**. So we bill primarily on duration, charge a small premium
for the Max model, and margin holds.

---

## 2. The Three Model Tiers

| UI Name | Real Model (configurable via env) | Positioning |
|---|---|---|
| **Lite** | `GEMINI_MODEL_LITE` (default: Gemini 3.1 Flash-Lite) | Maximum efficiency. High-throughput scripts. |
| **Balanced** | `GEMINI_MODEL_BALANCED` (default: Gemini 3.1 Flash) | Everyday workhorse. Great quality, low cost. |
| **Max** | `GEMINI_MODEL_MAX` (default: Gemini 3.5 Flash) | Frontier reasoning. Best, most creative scripts. |

> Never expose real model IDs to users. Only "Lite / Balanced / Max" appear in the UI.
> Real model IDs are env-configurable so we can swap the underlying Gemini model without a code change.

**Model availability by plan:**
- **Free** → Lite only. Balanced + Max **shown but locked** (greyed, tooltip: *"Unlock with Starter"* / *"Unlock with Pro"*).
- **Starter** → Lite + Balanced. Max shown locked (*"Unlock with Pro"*).
- **Pro** → All three. Max governed by monthly **Max Quota** (§4).
- **Agency** → All three. Large Max Quota.

---

## 3. Credit Cost Per Video

Base credit cost is set at the **Max** model. Lite/Balanced apply a discount multiplier.

**Base credits (Max model):**

| Duration | Credits | Real cost to us | Margin |
|---|---|---|---|
| 20s | 20 | $0.114 | 68% |
| 30s | 25 | $0.150 | 67% |
| 60s | 40 | $0.237 | 67% |
| 120s | 65 | $0.413 | 65% |
| 150s | 80 | $0.500 | 65% |

**Model multiplier:**

| Model | Multiplier |
|---|---|
| Lite | ×0.7 |
| Balanced | ×0.85 |
| Max | ×1.0 |

**Example:** 60s on Balanced = round(40 × 0.85) = **34 credits**. Max = **40**. Lite = **28**.

---

## 4. The Max Quota (Premium Lever)

Each paid plan includes a fixed number of **Max-model generations per month**. Once exhausted,
the model selector **auto-falls back to Balanced** for the rest of the cycle (user notified,
never blocked).

| Plan | Max generations/mo |
|---|---|
| Free | 0 (Lite only) |
| Starter | 0 (Lite + Balanced only) |
| Pro | 30 |
| Agency | 120 |

---

## 5. Subscription Plans

### Free — $0/mo
| | |
|---|---|
| Monthly credits | 30 |
| ≈ Videos | ~2 (20s) |
| Channels | 1 |
| Genres | 1 (Horror OR Brainrot, locked per channel) |
| Max duration | 20s |
| Models | Lite only (Balanced + Max shown locked) |
| Script char limit | 300 |
| TTS voices | 1 (locked per channel) |
| Scheduling | One 15-day block, manual renewal |
| Community voices | No |
| Top-ups | Yes |

### Starter — $19/mo *(or $190/yr — save $38)*
| | |
|---|---|
| Monthly credits | 850 |
| ≈ Videos | ~21 (60s) |
| Channels | 2 |
| Genres | Horror + Brainrot |
| Max duration | 60s (30s + 60s) |
| Models | Lite + Balanced (Max locked) |
| Script char limit | 900 |
| TTS voices | 3 per channel (premade) |
| Scheduling | Monthly auto-renewing blocks |
| Weekly seed prompt | Yes |
| Analytics | Basic |
| Community voices | No (Voice Vault add-on) |
| Worst-case margin | 72% |

### Pro — $49/mo *(or $490/yr — save $98)*
| | |
|---|---|
| Monthly credits | 2,600 |
| ≈ Videos | ~40 (120s) |
| Channels | 5 |
| Genres | Horror, Brainrot + custom |
| Max duration | 120s (30s, 60s, 120s) |
| Models | All. 30 Max gen/mo, then Balanced |
| Script char limit | 1,800 |
| TTS voices | All premade |
| Scheduling | Continuous / indefinite |
| Weekly seed prompt | Yes |
| Analytics | Advanced |
| Community voices | Yes — full library |
| Worst-case margin | 67% |

### Agency — $129/mo *(or $1,290/yr — save $258)*
| | |
|---|---|
| Monthly credits | 8,000 |
| ≈ Videos | ~100 (150s) |
| Channels | 15 |
| Genres | All + saved presets |
| Max duration | 150s (all 4 tiers) |
| Models | All. 120 Max gen/mo, then Balanced |
| Script char limit | 2,250 |
| TTS voices | All premade + community |
| Scheduling | Continuous + bulk |
| Team seats | 3 |
| Analytics | Full + cross-channel |
| Priority queue | Yes |
| White-label MP4 | Yes |
| Worst-case margin | 61% |

### Custom — Quote on Request
Inline expanding form below the four plan cards (not a modal/page). Fields: name, email,
channels needed, videos/mo, max duration, team seats, genres, notes. On submit → row in
`custom_plan_requests` (status `pending`) → admin provisions.

Internal quote floors (≥55% worst-case margin):
| Scale | Floor |
|---|---|
| 15–30 channels, 150–300 vids | $249–$349/mo |
| 30–50 channels, 300–500 vids | $449–$649/mo |
| 50+ / white-label reseller | Custom + setup fee |

---

## 6. AI Credit Top-Up Packs (every plan, incl. Free)

| Pack | Credits | Price | $/credit | Margin |
|---|---|---|---|---|
| Spark | 500 | $12 | $0.0240 | 74% |
| Boost | 1,500 | $32 | $0.0213 | 71% |
| Surge | 4,000 | $78 | $0.0195 | 68% |
| Blitz | 10,000 | $180 | $0.0180 | 65% |

> Top-up credits **never expire** while the account is active. Subscription credits reset
> monthly (no rollover except Pro/Agency: 1-month rollover).

---

## 7. Add-On Packs (Feature Unlocks, Monthly)

| Add-On | Price | Effect | Available to |
|---|---|---|---|
| Voice Vault | +$9/mo | Full ElevenLabs community voice library | Starter |
| Max Booster | +$15/mo | +50 Max generations before fallback | Pro, Agency |
| Extra Channel | +$6/mo | +1 channel beyond plan limit | Starter, Pro |
| Priority Queue | +$12/mo | Jump the generation queue | Starter, Pro |

---

## 8. Plan Comparison (Master Table)

| | Free | Starter | Pro | Agency | Custom |
|---|---|---|---|---|---|
| Price | $0 | $19/mo | $49/mo | $129/mo | Quote |
| Credits/mo | 30 | 850 | 2,600 | 8,000 | Custom |
| ≈ Videos | 2 | 21 | 40 | 100 | Custom |
| Channels | 1 | 2 | 5 | 15 | Custom |
| Max duration | 20s | 60s | 120s | 150s | ≤150s |
| Models | Lite | Lite+Bal | All (30 Max) | All (120 Max) | All |
| Custom genre | No | No | Yes | Yes | Yes |
| Community voices | No | Add-on | Yes | Yes | Yes |
| Scheduling | 15d manual | Monthly | Continuous | Bulk | Bulk |
| Team seats | 1 | 1 | 1 | 3 | Custom |
| Top-ups | Yes | Yes | Yes | Yes | Yes |
| Worst-case margin | — | 72% | 67% | 61% | ≥55% |

---

## 9. Asset Cost Model (backs the credit math)

| Asset | Source | Cost/video | Notes |
|---|---|---|---|
| Images (Horror) | Imagen 4 Fast (Google AI Studio) | $0.005–$0.02/img | swappable → Z-Image Turbo $0.01 / GPT Image 1 Mini $0.005 |
| Footage (Brainrot) | Self-hosted CC0 satisfying loops | $0 | curated library, rotated |
| Music | Self-hosted CC0 (Pixabay/FMA) | $0 | mood buckets, rotated |
| Captions | ElevenLabs word timestamps → ASS → FFmpeg | $0 | Whisper fallback |
| Voice | ElevenLabs `eleven_flash_v2_5` | $103 / 1M chars | ~15 chars/sec narration |
| Script/SEO | Gemini (Lite/Balanced/Max) | <$0.01 | tier delta negligible |

Voice cost per char: `FLASH_COST_PER_CHAR = 103 / 1_000_000` (= $0.000103/char).

---

## 10. Constants (mirrored in `backend/app/core/pricing.py`)

```python
CREDIT_RETAIL_RATE = 0.018             # $/credit at base subscription tier
REAL_COST_PER_CREDIT_WORST = 0.00625   # internal, margin tracking

VIDEO_CREDITS_BASE = {                 # at Max model
    "20s": 20, "30s": 25, "60s": 40, "120s": 65, "150s": 80
}
MODEL_MULTIPLIER = {"Lite": 0.7, "Balanced": 0.85, "Max": 1.0}

def credits_for_video(duration, model):
    return round(VIDEO_CREDITS_BASE[duration] * MODEL_MULTIPLIER[model])

PLAN_CREDITS = {"Free": 30, "Starter": 850, "Pro": 2600, "Agency": 8000}
MAX_QUOTA    = {"Free": 0, "Starter": 0, "Pro": 30, "Agency": 120}

TOPUP_PACKS = {   # name: (credits, price_usd)
    "Spark": (500, 12), "Boost": (1500, 32),
    "Surge": (4000, 78), "Blitz": (10000, 180),
}

FLASH_COST_PER_CHAR = 103 / 1_000_000

DURATION_CHARS = {  # ~15 chars/sec, target for script trimming
    "20s": 300, "30s": 450, "60s": 900, "120s": 1800, "150s": 2250
}
```

---

*Last updated: 2026-06-16. Final credit calibration pending client sign-off after full E2E works.*
