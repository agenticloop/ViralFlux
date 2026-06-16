Viral Flux.

I am rethinking the entire strategy, here so lets roll what we gotta do is make it in a fully working condition till what we have thought for. 

Core functionality: 
- I want to use the google gemini 3.5 flash model for script generation and whatever text based LLM call we need, no openai 
so remove openai from the code completely and dead code as well like a good developer. 

- Reddit api is not needed at all when I think in retrospect, 
first tell me if the LLM is set already for script writing 
then why we needded the reddit api ?? 
From what I think, we can have an option of an give an idea 
about generating a script as well manually for each short that
we are planning to do, so technically not just horror 
we can do it for more stuff as well no? 




TTS: {{{{
# ElevenLabs TTS — Integration Brief

## Overview
Integrate ElevenLabs TTS into a YouTube Shorts generation SaaS.
Two genres: **Horror** and **Brainrot**.
Four duration tiers per short: **30s / 60s / 120s / 150s**.

---

## API

**Endpoint:** `POST https://api.elevenlabs.io/v1/text-to-speech/{voice_id}`
**Auth header:** `xi-api-key: YOUR_KEY`
**Model to use:** `eleven_flash_v2_5` (cheapest, sufficient quality)
**Response:** Binary MP3 audio stream

```json
{
  "text": "Your narration script here",
  "model_id": "eleven_flash_v2_5",
  "voice_settings": {
    "stability": 0.35,
    "similarity_boost": 0.75,
    "style": 0.40,
    "use_speaker_boost": true
  }
}
```

> Voice IDs for premade voices below are stable but verify via `GET /v1/voices` on first boot and cache locally.

---

## Pricing (Flash model only — always use this)

| Model | Rate | Credits/char |
|---|---|---|
| `eleven_flash_v2_5` | **$103 / 1M chars** | 0.5 credits |

**Do NOT use** `eleven_multilingual_v2` or `eleven_v3` — they cost 2x and aren't needed here.

---

## Duration Tiers → Character Budget

Narration pace: ~15 chars/second

| Tier | Duration | Est. Characters | Est. Cost (Flash) |
|---|---|---|---|
| Short-Half | 30s | ~450 chars | ~$0.05 |
| Short-Full | 60s | ~900 chars | ~$0.09 |
| Long-Half | 120s | ~1,800 chars | ~$0.19 |
| Long-Full | 150s | ~2,250 chars | ~$0.23 |

> Script generation should target these character counts. Pad or trim the script to fit the selected tier before sending to TTS.

---

## Genre: HORROR

Voice settings for horror:
```json
{ "stability": 0.35, "similarity_boost": 0.75, "style": 0.45, "use_speaker_boost": true }
```

| Voice Name | Voice ID | Description |
|---|---|---|
| Bill | `pqHfZKP75CvOlQylNhV4` | Deep, powerful American male. Commanding and dark. Best default horror narrator. |
| Daniel | `onwK4e9ZLuTAKqWW03F9` | Deep British male. Slow, deliberate, formal. Sounds like a true crime documentary gone wrong. |
| Callum | `N2lVS1w4EtoT3dr4eOWO` | Hoarse, intense, middle-aged male. Unsettling energy. Great for disturbing monologues. |
| Fin | `D38z5RcWu1voky8WS1ja` | Old raspy male. Gritty and worn. Sounds like someone who has seen too much. |
| Harry | `SOYHLrjzK2X1ezoPC6cr` | Warm but anxious male. Works for first-person terror and paranoia narration. |
| Arnold | `VR6AewLTigWG4xSOukaG` | Crisp American narrator. Good for horror documentary / "based on true events" style. |
| Clyde | `2EiwWnXFnvU5JabPnv8n` | Middle-aged American male. Slightly eerie undertone. Reliable for suspense narration. |
| Glinda | `z9fAnlkpzviPz146aGWa` | Dark female voice. Sinister and theatrical. Good for supernatural / witch-style horror. |
| Thomas | `GBv7mTt0atIp3Br8iCZE` | Calm, deep American. Works well for slow-burn psychological horror. |

---

## Genre: BRAINROT

Brainrot = chaotic, deadpan, unhinged, high-energy or ironically monotone narration style.

Voice settings for brainrot:
```json
{ "stability": 0.25, "similarity_boost": 0.70, "style": 0.65, "use_speaker_boost": true }
```

Lower stability = more chaotic variation between sentences. Higher style = more expressive and dramatic.

| Voice Name | Voice ID | Description |
|---|---|---|
| Adam | `pNInz6obpgDQGcFmaJgB` | Deep, intense narrator. Ironically serious energy — perfect for overdramatic brainrot commentary. |
| Liam | `TX3LPaxmHKxFdv7VOQHJ` | Young, articulate American. Fast and expressive. Good for chaotic gaming/meme narration. |
| Sam | `yoZ06aMxZJJ28mfd3POQ` | Raspy and low. Deadpan delivery that hits for brainrot. |
| Charlie | `IKne3meq5aSn9XLyUdCD` | Casual English male. Unhinged British-style commentary energy. |
| Antoni | `ErXwobaYiN019PkySvjV` | Natural, well-rounded. Reliable for conversational brainrot scripts. |
| Ethan | `g5CIjZEefAph4nQFvHAz` | ASMR-adjacent whisper. Unsettling enough for crossover horror-brainrot content. |
| Patrick | `ODq5zmih8GrVes37Dx0d` | Confident, composed American. Works for ironically calm narration over absurd content. |

---

## Voice Pricing Note

**All voices above cost the same.** Pricing is determined only by model (`eleven_flash_v2_5`), not by which voice is selected. No special billing per voice.

---

## SaaS Credit Tracking

To track cost per generation in your SaaS:

```python
FLASH_COST_PER_CHAR = 103 / 1_000_000  # $0.000103

def calculate_tts_cost(script: str) -> float:
    return len(script) * FLASH_COST_PER_CHAR

# Example:
cost = calculate_tts_cost("It was a dark and stormy night...")
# → tracks actual cost to show users or deduct from their credit balance
```

---

## Voice Library (Community Voices)

ElevenLabs has 10,000+ community voices for horror/dark/brainrot categories.
These are **not available by default** — they must be added to the account first via the Voice Library UI or `POST /v1/voices/{voice_id}/add`.

Once added, they appear in `GET /v1/voices` and can be used exactly like premade voices above.

For discovering community voices programmatically:
`GET https://api.elevenlabs.io/v1/shared-voices?category=premade&featured=true&gender=male&language=en`

This lets users browse and add voices directly from within the SaaS in the future.

---

## Implementation Checklist

- [ ] On app start: fetch `/v1/voices`, cache voice list with IDs locally
- [ ] Map genre selector → recommended voice list (from tables above)
- [ ] Map duration tier → character limit for script trimming before TTS call
- [ ] Always use `eleven_flash_v2_5` as model_id
- [ ] Track `len(script)` per call to log cost
- [ ] Apply genre-specific voice settings (stability/style differ between horror and brainrot)
- [ ] Return MP3 from API → feed directly into FFmpeg pipeline for stitching

Also must make sure We want to have those community voices as well from eleven labs easily if we want to later add it our application so keep in mind that too as well. 
We dont want any other TTS. 
}}}}



I want a true multi-tenant system, where an individual account can create multiple channels according to their chosen plan, and for each of their channel can choose genre of 
content and posting timmings, and the posting schedule, and the seed short prompt as welll weekly, like to generate what kind of that genre scripts so gemini model can get that 
seed with full creativity and make it happen according to that script as well. 


All youtube channels can be seen, individual user account need to connect with youtube via youtube google's oauth connect button (no postproxy for viralflux, direct we want to have that 
kind of outh app where our users can connect to their youtube channels no matter which google account their channels users have their channel, for example if a user have 4 channels for autoposting which are created in 4 different google accounts they can do that and would be properly saved there as well. 


Now as you know our viralflux design is very user friendly UI/UX kit, to maintain that we can have multiple dashboard tabs to manage everything, and from top menu one can choose 
their channel (like workspace change people do). 


Now here is the thing we want to have our own AI credits system that we will calculate at last when i say so after we are done with everyhting and whole product works, so maintain 
pricing.md for everything as we plan along each service. 


So now you know we are removing postproxy, google's tts, removing OpenAI, edge TTS, using ( gemini 3.5 flash model,   Gemini 3.1 Flash-Lite), removing ,  from the Viralflux,




N8N should be in such a way that it doesnt have problems with our multi-tenancy and can not burden the server as well, and works like production ready, and should be used as a maximum 
proper working automator. So our SaaS is the best for everybody. 




Plans and Pricing{{{{

# ViralFlux — Pricing & Credits Manifesto

> The single source of truth for plans, the AI credit system, model tiers, add-ons, and unit economics.
> Every number here is empirically derived from real API costs. Nothing is guessed.

---

## 1. The Core Principle

Users never see tokens, characters, or API costs. They see **credits** and **videos**.
Behind the scenes, every credit maps to a fixed, known real cost — so it is never a gamble for us or for them.

- **1 credit ≈ $0.018 retail value** (the rate at the base subscription tier)
- **Real cost backing 1 credit ≈ $0.00625** (worst case, Max model)
- **Baked-in blended margin: 60–74%** across every plan, pack, and add-on

The genius of the system: the LLM model tier barely affects our real cost (the LLM is <$0.01/video). The real cost is **images + voice**, both driven by **video duration**. So we bill primarily on duration, charge a small premium for the Max model, and the margin holds no matter what the user does.

---

## 2. The Three Model Tiers

| UI Name | Real Model | Input /1M | Output /1M | Positioning |
|---|---|---|---|---|
| **Lite** | Gemini 3.1 Flash-Lite | $0.25 | $1.50 | Maximum efficiency. High-throughput, lightweight scripts. |
| **Balanced** | Gemini 3.1 Flash | $0.50 | $3.00 | Everyday workhorse. Great quality, low cost. |
| **Max** | Gemini 3.5 Flash | $1.50 | $9.00 | Frontier reasoning. Best scripts, most creative. |

> Never expose real model IDs to users. Only "Lite / Balanced / Max" appear in the UI.

**Model availability by plan:**
- **Free** → Lite only. Balanced and Max are **shown but locked** (greyed, hover tooltip: *"Unlock with Starter"* / *"Unlock with Pro"*).
- **Starter** → Lite + Balanced. Max shown locked (*"Unlock with Pro"*).
- **Pro** → All three. Max governed by monthly **Max Quota** (see §4).
- **Agency** → All three. Large Max Quota.

---

## 3. Credit Cost Per Video

Base credit cost is set at the **Max** model. Lite and Balanced apply a discount multiplier — so choosing a cheaper model genuinely costs the user fewer credits (rewards efficient behaviour, protects our margin either way).

**Base credits (Max model):**

| Duration | Credits | Real cost to us | Our margin |
|---|---|---|---|
| 20s | 20 | $0.114 | 68% |
| 30s | 25 | $0.150 | 67% |
| 60s | 40 | $0.237 | 67% |
| 120s | 65 | $0.413 | 65% |
| 150s | 80 | $0.500 | 65% |

**Model multiplier (applied to base):**

| Model | Multiplier | Effect |
|---|---|---|
| Lite | ×0.7 | Cheapest — fewest credits per video |
| Balanced | ×0.85 | Mid |
| Max | ×1.0 | Full base cost |

**Example:** a 60s video on Balanced = 40 × 0.85 = **34 credits**. On Max = **40 credits**. On Lite = **28 credits**.

---

## 4. The Max Quota (Premium Lever)

Each paid plan includes a fixed number of **Max-model generations per month**. Once exhausted, the model selector **auto-falls back to Balanced** for the rest of the cycle (the user is notified, never blocked — their videos still generate, just on Balanced).

This is the primary upsell driver. It costs us almost nothing in real terms (the LLM delta is tiny), but it makes higher plans feel premium and gives a concrete reason to upgrade or buy a **Max Booster** add-on.

| Plan | Max generations/mo included |
|---|---|
| Free | 0 (Lite only) |
| Starter | 0 (Lite + Balanced only) |
| Pro | 30 |
| Agency | 120 |

---

## 5. Subscription Plans

All plans are credit-allowanced. Video counts shown are estimates at the plan's typical duration — the user can always make more shorter videos or fewer longer ones.

---

### Free — $0/mo

| | |
|---|---|
| **Monthly credits** | 30 |
| **≈ Videos** | ~2 (20s each) |
| **Channels** | 1 |
| **Genres** | 1 (Horror OR Brainrot, locked per channel) |
| **Max duration** | 20s |
| **Models** | Lite only (Balanced + Max shown locked) |
| **Script char limit** | 300 |
| **TTS voices** | 1 (locked per channel) |
| **Scheduling** | One 15-day block, manual renewal, no auto-roll |
| **Community voices** | No |
| **Can buy top-ups?** | Yes (Spark pack and up) |

**Our cost:** ~$0.19/mo per active free user. Pure acquisition spend.

---

### Starter — $19/mo *(or $190/yr — save $38)*

| | |
|---|---|
| **Monthly credits** | 850 |
| **≈ Videos** | ~21 (60s each) → **$0.89/video perceived** |
| **Channels** | 2 |
| **Genres** | Horror + Brainrot |
| **Max duration** | 60s (30s + 60s tiers) |
| **Models** | Lite + Balanced (Max locked) |
| **Script char limit** | 900 |
| **TTS voices** | 3 per channel (premade) |
| **Scheduling** | Monthly auto-renewing blocks |
| **Weekly seed prompt** | Yes |
| **Analytics** | Basic |
| **Community voices** | No (add via Voice Vault add-on) |

**Worst-case margin: 72%** (all 850 credits burned at Max-equivalent cost).

---

### Pro — $49/mo *(or $490/yr — save $98)*

| | |
|---|---|
| **Monthly credits** | 2,600 |
| **≈ Videos** | ~40 (120s each) → **$1.23/video perceived** |
| **Channels** | 5 |
| **Genres** | Horror, Brainrot + any custom genre |
| **Max duration** | 120s (30s, 60s, 120s) |
| **Models** | All three. **30 Max generations/mo**, then Balanced fallback |
| **Script char limit** | 1,800 |
| **TTS voices** | All premade |
| **Scheduling** | Continuous / indefinite |
| **Weekly seed prompt** | Yes |
| **Analytics** | Advanced |
| **Community voices** | Yes — full library |

**Worst-case margin: 67%.**

---

### Agency — $129/mo *(or $1,290/yr — save $258)*

| | |
|---|---|
| **Monthly credits** | 8,000 |
| **≈ Videos** | ~100 (150s each) → **$1.29/video perceived** |
| **Channels** | 15 |
| **Genres** | All + saved genre presets |
| **Max duration** | 150s (all 4 tiers) |
| **Models** | All three. **120 Max generations/mo**, then Balanced fallback |
| **Script char limit** | 2,250 |
| **TTS voices** | All premade + full community library |
| **Scheduling** | Continuous + bulk across channels |
| **Team seats** | 3 |
| **Analytics** | Full + cross-channel |
| **Priority queue** | Yes |
| **White-label MP4** | Yes |

**Worst-case margin: 61%.**

---

### Custom — Quote on Request

A button **below** the four plan cards expands an inline form (not a modal, not a new page). Fields: name, email, channels needed, videos/mo, max duration, team seats, genres, notes. On submit → row in `custom_plan_requests` (status `pending`) → admin reviews and provisions a bespoke subscription.

**Internal quote floors (maintain ≥55% worst-case margin):**

| Scale | Floor price |
|---|---|
| 15–30 channels, 150–300 vids | $249–$349/mo |
| 30–50 channels, 300–500 vids | $449–$649/mo |
| 50+ / white-label reseller | Custom + setup fee |

---

## 6. AI Credit Top-Up Packs

Available to **every plan including Free**. Volume discount built in — bigger packs are cheaper per credit, but all stay highly profitable. The smallest pack is priced *above* the subscription credit rate, so subscribing always looks like the smarter deal.

| Pack | Credits | Price | $/credit | Our margin |
|---|---|---|---|---|
| **Spark** | 500 | $12 | $0.0240 | 74% |
| **Boost** | 1,500 | $32 | $0.0213 | 71% |
| **Surge** | 4,000 | $78 | $0.0195 | 68% |
| **Blitz** | 10,000 | $180 | $0.0180 | 65% |

> Credits from top-ups **never expire** while the account is active. Subscription credits reset monthly (no rollover except Pro/Agency: 1-month rollover).

---

## 7. Add-On Packs (Feature Unlocks, Monthly)

These are pure-margin recurring revenue — they unlock capability, not credits.

| Add-On | Price | What it does | Available to |
|---|---|---|---|
| **Voice Vault** | +$9/mo | Unlocks full ElevenLabs community voice library | Starter |
| **Max Booster** | +$15/mo | +50 Max-model generations before fallback | Pro, Agency |
| **Extra Channel** | +$6/mo | One additional channel beyond plan limit | Starter, Pro |
| **Priority Queue** | +$12/mo | Jump the generation queue | Starter, Pro |

---

## 8. Plan Comparison (Master Table)

| | Free | Starter | Pro | Agency | Custom |
|---|---|---|---|---|---|
| **Price** | $0 | $19/mo | $49/mo | $129/mo | Quote |
| **Credits/mo** | 30 | 850 | 2,600 | 8,000 | Custom |
| **≈ Videos** | 2 | 21 | 40 | 100 | Custom |
| **Channels** | 1 | 2 | 5 | 15 | Custom |
| **Max duration** | 20s | 60s | 120s | 150s | ≤150s |
| **Models** | Lite | Lite+Bal | All (30 Max) | All (120 Max) | All |
| **Custom genre** | No | No | Yes | Yes | Yes |
| **Community voices** | No | Add-on | Yes | Yes | Yes |
| **Scheduling** | 15d manual | Monthly | Continuous | Bulk | Bulk |
| **Team seats** | 1 | 1 | 1 | 3 | Custom |
| **Top-ups** | Yes | Yes | Yes | Yes | Yes |
| **Worst-case margin** | — | 72% | 67% | 61% | ≥55% |

---

## 9. Why Users Feel It's Cheap (and We Still Win)

- **Perceived price per video is $0.89–$1.29** — absurdly cheap for a fully automated, narrated, scheduled, auto-posted YouTube Short. The real alternative (freelancer or manual editing) is $10–50/video.
- **Credits feel abundant** — 850, 2,600, 8,000 are big satisfying numbers.
- **Choosing Lite/Balanced "saves" them credits** — they feel in control and economical, while every path keeps us at 50–74% margin.
- **Top-ups remove the ceiling** — no hard wall, no frustration; just buy more, always profitably.
- **The Max Quota creates natural upgrade pressure** without ever blocking output.

---

## 10. Constants for Implementation

```python
CREDIT_RETAIL_RATE = 0.018             # $/credit at base subscription tier
REAL_COST_PER_CREDIT_WORST = 0.00625   # internal, for margin tracking

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
```

---

*Last updated: June 2026. Recalculate every table whenever an API rate or the model stack changes.*

}}}}





Stripe we will later after we are done with everything adn testing. 


{{{ 
# ViralFlux — Asset Sourcing & Pipeline Brief

How we get every visual + audio asset, cheapest reliable source for each, and the legal reality.

---

## Summary Table

| Asset | Source | Cost per video | Method |
|---|---|---|---|
| **Images** | Imagen 4 Fast (Google) or Z-Image Turbo | $0.005–$0.02/img | Generate per scene |
| **Background music** | Curated CC0 library (self-hosted) | **$0** | License once, rotate |
| **Brainrot footage** | Curated loop library (self-hosted) | **$0** | ⚠️ see legal note |
| **Moving subtitles** | captacity (open-source, Whisper) | **$0** | Self-hosted, burn-in |

Only images carry a real per-video cost. Music, footage, and captions are all **~$0/video** once set up.

---

## 1. IMAGES — Generate, don't source

Sourcing stock per-scene is slow and inconsistent. Generate instead. Cheapest reliable options as of 2026:

| Model | Cost/image | Notes |
|---|---|---|
| FLUX Schnell (self-host) | $0.003 | Cheapest, needs a GPU pod |
| GPT Image 1 Mini | $0.005 | Cheapest hosted, high quality |
| Z-Image Turbo | $0.01 | Good for 1024×1024 drafts |
| **Imagen 4 Fast (Google)** | **$0.02** | Stays in your AI Studio key, clean quality |

**Recommendation:** Start with **Imagen 4 Fast** ($0.02) since you're already on the Google AI Studio key — one key, one bill, no new vendor. If image cost ever bites at scale, drop to **Z-Image Turbo ($0.01)** or **GPT Image 1 Mini ($0.005)** by swapping one API call. The pipeline shouldn't care which model produced the image.

**Consistency across scenes:** lock a style prefix in every prompt + reuse the same seed per video. For horror this is easy (atmospheric scenes, no fixed character). Brainrot doesn't even need generated images if you're using gameplay footage (see §3).

---

## 2. MUSIC — License a library once, never pay per video

Do **not** generate music per video (slow, adds cost, quality gamble). Build a **curated royalty-free library**, host it, and have the pipeline pick a mood-matched track.

**The key distinction for a SaaS:** you are *redistributing* music to your users, not just using it yourself. That means you need tracks cleared for **redistribution**, which rules out most "free for creators" libraries. Safest tier:

| Source | License | SaaS-safe? |
|---|---|---|
| **Pixabay Music** | CC0-style, no attribution | ✅ Best for redistribution |
| **Free Music Archive (CC0 tracks)** | CC0 / public domain | ✅ |
| YouTube Audio Library | Free, but for *YouTube use* | ⚠️ Fine since output goes to YouTube, but don't let users download raw |
| Uppbeat / Soundstripe / Artlist | Subscription, per-seat | ❌ Not for SaaS redistribution without enterprise license |

**Plan:** hand-pick ~40–60 CC0 tracks — split into mood buckets (Horror: dark ambient, drone, tension; Brainrot: upbeat, phonk, hype). Store them, tag by mood, rotate randomly per video so channels don't sound repetitive. **One-time effort, $0 ongoing.**

> If you later want unique-per-video music, add a Suno/Udio-style generator as a premium add-on. Not needed for launch.

---

## 3. BRAINROT FOOTAGE — ⚠️ Read this carefully

This is the one place with real legal exposure, so I'm being blunt.

**Subway Surfers and Minecraft footage is NOT copyright-free.** Subway Surfers is owned by SYBO; Minecraft by Mojang/Microsoft. Every "no copyright Subway Surfers gameplay" upload on YouTube is either infringement or relies on a shaky fair-use argument. Competitors (Revid, etc.) use it anyway and claim *"fair use when combined with transformative content"* — that argument is **legally untested and risky for a paid SaaS** that's commercially redistributing the footage to thousands of users. If SYBO or Microsoft ever sends a takedown or claim, it lands on you and every channel using your tool.

**Your three real options:**

1. **Use it like competitors do** — accept the gray-area risk. It's the industry norm right now and enforcement has been rare. But it *is* a risk, and it scales with your user count.

2. **Use genuinely free "satisfying loop" footage** *(recommended for safety)* — the brainrot format works with ANY hypnotic background, not just gameplay. CC0 sources (Pixabay Video, Pexels, Mixkit) have tons of: hydraulic press, soap cutting, kinetic sand, paint mixing, marble runs, ASMR loops, oddly-satisfying compilations. These deliver the same dopamine-retention effect with **zero IP risk**. Build a curated loop library exactly like the music one.

3. **Generate your own parkour-style loops** — AI video (Veo, Kling) or even simple procedural 3D loops you own outright. Higher effort, fully clean.

**My recommendation:** launch with **option 2** (curated CC0 satisfying loops) as the default, and treat actual gameplay footage as a clearly-labelled "use at your own risk" toggle if you offer it at all. Protects you and your users.

---

## 4. MOVING SUBTITLES — Open-source, free, exactly the viral style

The bouncing word-by-word highlighted captions on every Short/TikTok are solved by free tooling. No paid service needed.

**Use `captacity`** (open-source: github.com/unconv/captacity) — Whisper + MoviePy. It does word-level timing and the yellow/red highlight-current-word style out of the box:

```python
captacity.add_captions(
    video_file="short.mp4",
    output_file="short_captioned.mp4",
    font_size=130, font_color="yellow",
    stroke_width=3, stroke_color="black",
    highlight_current_word=True,
    word_highlight_color="red",
    line_count=1,
)
```

**Even better — you may skip Whisper entirely.** ElevenLabs can return **word-level timestamps** with the audio it generates. Feed those timestamps straight into an ASS subtitle file and burn it with FFmpeg. That's more accurate than re-transcribing (no speech-to-text errors) and faster. Use Whisper only as a fallback.

**Styling per genre:** bold energetic font + heavy stroke for brainrot; cleaner slower-fade captions for horror. Store 2–3 caption style presets and pick by genre. **$0 per video, just compute.**

---

## Final Pipeline (assets integrated)

```
Seed prompt + genre + duration
        ↓
Gemini (Lite/Balanced/Max) → script + scene breakdown + image prompts
        ↓
HORROR path:                          BRAINROT path:
Imagen 4 Fast → scene images          Pull CC0 satisfying-loop from library
        ↓                                     ↓
ElevenLabs Flash → narration + word timestamps (both paths)
        ↓
Pick mood-matched CC0 music track from library
        ↓
FFmpeg: images/loop + voice + music (ducked) + burned word-by-word captions
        ↓
MP4 → YouTube Data API upload
```

---

## Cost Impact on pricing.md

Music, footage, and captions add **$0/video**. Only images matter, already in the cost model. No change to margins.

If you switch images Imagen 4 Fast ($0.02) → Z-Image Turbo ($0.01), per-video cost drops ~$0.06–0.24 depending on duration — pure extra margin or room to give users more value.

---

*Last updated: June 2026.*
}}}
