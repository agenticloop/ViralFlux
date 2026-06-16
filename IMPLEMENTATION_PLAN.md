# ViralFlux v2 — Implementation Plan (Re-Architecture)

> Derived from `plan.md`. Source of truth for the autonomous overnight build.
> Mode: **fully autonomous**, commit at each working milestone. Keys stay **placeholders**
> (no live external calls) — everything built to run correctly the moment real keys drop in.
> Priority if time-boxed: **backend pipeline first**, frontend/UX polish last.

## North Star
A true multi-tenant YouTube Shorts automation SaaS:
account → many channels (per plan) → each channel has a genre, ElevenLabs voice, posting
schedule, and a weekly seed prompt. Gemini (Lite/Balanced/Max) writes scripts (or user
supplies them manually). ElevenLabs narrates. Imagen/CC0 supplies visuals. FFmpeg assembles
with burned word-by-word captions. Direct Google OAuth posts to each channel's own YouTube
(multi-Google-account). Everything metered in **credits**.

## Vendor Decisions (final)
**KEEP:** FastAPI, Postgres, SQLAlchemy async, Celery, Redis, Next.js, Resend (email),
Gemini, ElevenLabs, YouTube Data API (direct), FFmpeg, n8n, Nginx, Docker.
**REMOVE (dead code, fully):** OpenAI/GPT, Reddit/PRAW, PostProxy, edge-tts, Google Cloud TTS,
Pexels/Pixabay/Unsplash stock sourcing.
**ADD:** Imagen 4 Fast image gen (swappable), CC0 footage library (brainrot), credits system,
direct multi-account YouTube OAuth, ElevenLabs word-timestamp captions.

---

## Phase 0 — Purge dead code & vendors
- Delete services: `llm/openai_svc.py`, `reddit_service.py`, `postproxy_service.py`,
  `tts/edge_tts.py`, `tts/google_tts.py`, `assets/pexels.py`, `assets/pixabay.py`.
- Delete tasks: `discover_trending_topics`; remove Reddit/trending paths.
- Remove config keys: `OPENAI_*`, `REDDIT_*`, `POSTPROXY_API_KEY`, `GOOGLE_TTS_API_KEY`,
  `PEXELS_API_KEY`, `PIXABAY_API_KEY`, `UNSPLASH_ACCESS_KEY`.
- Remove from `requirements.txt`: openai, praw, edge-tts, google-cloud-texttospeech.
- Frontend: remove OpenAI voice provider, edge-tts defaults, Reddit/trending UI.
- n8n: delete `trend_discovery.json`.
- Clean `.env`, `.env.example`, `docker-compose.yml`, docs.
- **Gate:** backend imports clean, no references to removed modules (grep).

## Phase 1 — Data model & migrations (multi-tenant + credits)
- **Plan** model rewrite → Free/Starter/Pro/Agency with: credits_per_month, channels_limit,
  max_quota, max_duration_sec, models_allowed, genres_allowed, script_char_limit,
  community_voices, team_seats, price_monthly, price_yearly, addons. Seed all four.
- **Credits:** add to user (or `credit_accounts`): subscription_credits, topup_credits,
  max_quota_used, period_start/end. `credit_transactions` ledger (grant/topup/spend/refund).
  `topup_purchases`, `addon_subscriptions`, `custom_plan_requests`.
- **YoutubeChannel:** add genre, seed_prompt, seed_prompt_updated_at, model_tier (default),
  duration_default, voice_id, voice_name, google_account_email, youtube_channel_title,
  youtube_thumbnail_url; **drop** postproxy_profile_id, default_format, default_voice_provider
  (edge defaults). Keep encrypted oauth tokens.
- **VideoJob:** add genre, duration_tier, model_tier, script_source(manual|seed|ai),
  credits_cost(int), voice_settings(JSON), word_timestamps(JSON). Keep cost_usd for internal.
- Genre config (horror/brainrot/custom) with default voice settings.
- Regenerate clean initial Alembic migration (pre-launch; seed runs on boot).
- **Gate:** `alembic upgrade head` + seed runs on a fresh DB.

## Phase 2 — LLM: Gemini-only, 3 tiers
- Refactor `llm/gemini.py`: `GEMINI_MODEL_LITE/BALANCED/MAX` env (defaults = plan's intended
  IDs), tier→model resolver. Single `GeminiService` used everywhere.
- Methods: `generate_script(genre, seed/topic, duration_tier, model_tier)` →
  script + scene breakdown + per-scene image prompts; `generate_seo()` (title/desc/tags) —
  now Gemini, not OpenAI. Trim/pad script to `DURATION_CHARS[tier]`.
- Genre-aware prompt templates (horror, brainrot, custom).
- **Gate:** unit test with mocked Gemini client returns well-formed script JSON.

## Phase 3 — TTS: ElevenLabs-only
- Rewrite `tts/elevenlabs.py`: model `eleven_flash_v2_5`; genre voice settings
  (horror vs brainrot from plan.md); **word-level timestamps** endpoint; cost = `len*FLASH_COST_PER_CHAR`.
- Voice catalog: seed premade horror/brainrot voices (IDs from plan.md). Boot-time
  `GET /v1/voices` fetch + cache (graceful no-op without key). Community-voice add hook
  (`POST /v1/voices/{id}/add`) + `shared-voices` browse for future.
- **Gate:** unit test with mocked client returns audio bytes + timestamps + correct cost.

## Phase 4 — Assets: Imagen + CC0 libraries + captions
- `assets/image_service.py`: Imagen 4 Fast (Google AI Studio key), locked style prefix +
  per-video seed for scene consistency. Provider interface (swap → Z-Image/GPT Image Mini).
- `assets/footage_library.py`: CC0 satisfying-loop library for brainrot (assets/footage/<bucket>),
  tag + rotate. Seed script + READMEs (like music).
- `assets/music_library.py`: expand mood buckets per genre, rotation.
- `video/captions.py`: ElevenLabs word timestamps → ASS subtitle (genre style presets:
  bold/energetic brainrot, clean/slow horror) → FFmpeg burn. Whisper fallback retained.
- **Gate:** ASS generated from sample timestamps; image/footage selection unit-tested.

## Phase 5 — Video pipeline rewire
- `video/pipeline.py`: branch by genre — Horror = Imagen scenes + ken-burns;
  Brainrot = CC0 loop footage. Both: ElevenLabs voice → word timestamps → burned captions →
  mood-matched CC0 music (ducked) → FFmpeg assemble at 1080×1920 for the duration tier.
- Output MP4 → media/previews → approval flow.
- **Gate:** pipeline runs end-to-end with all external calls mocked, produces a valid MP4 plan
  (or real MP4 if ffmpeg available with placeholder assets).

## Phase 6 — YouTube direct OAuth (multi-account)
- `youtube_service.py`: our OAuth app. Per-channel connect → Google consent URL →
  callback stores encrypted tokens + google_account_email + youtube_channel_title/thumbnail.
  One user, N channels, each possibly a different Google account. Token refresh. Upload via
  Data API. **Remove** all PostProxy paths from `upload_to_youtube`.
- Channels API: `POST /{id}/connect-youtube` → consent URL; `GET /youtube/callback`.
- **Gate:** OAuth URL builds; callback stores tokens (mocked exchange); upload path unit-tested.

## Phase 7 — Credits enforcement & pricing logic
- `core/pricing.py` mirrors `pricing.md` constants. `credits_for_video(duration, model)`.
- On subscription: grant monthly credits + reset Max quota (Pro/Agency 1-mo rollover).
- Generation: check balance → reserve → on success spend + ledger entry; Max quota tracking
  with auto-fallback to Balanced + user notice; insufficient → block w/ top-up CTA (never
  hard wall: top-ups available to all).
- Top-up & add-on application endpoints (Stripe deferred — provision via admin/manual now).
- **Gate:** unit tests: credit math, quota fallback, ledger correctness.

## Phase 8 — Scheduling & automation (Celery beat primary, n8n light)
- Celery beat: DB-driven scan of `channel_schedules`, enqueue due per-channel generations
  (tenant-safe row locks, idempotency, no server burden). Weekly seed-prompt rotation.
- n8n reworked: NO per-tenant state; workflows call backend internal endpoints
  (approval reminders, analytics sync trigger). Single lightweight poller pattern. Remove
  trend discovery. Document multi-tenant safety.
- **Gate:** beat schedule registers; due-job query returns correct per-channel jobs.

## Phase 9 — Frontend
- **Channel switcher** in topbar (workspace-style; uses `uiStore.selectedChannelId`).
- **Generate flow:** genre, duration tier, model tier (locked states + tooltips), voice
  picker, script source (manual textarea vs seed/AI). Credits cost preview (not $).
- **Channel settings:** genre, weekly seed prompt, schedule/timings, voice, default model.
- **Credits UI:** balance, ledger, usage; replace $ cost displays.
- **Pricing page:** Free/Starter/Pro/Agency + top-up packs + add-ons + Custom inline form.
- **YouTube connect** button per channel (direct OAuth), shows connected Google account.
- Remove OpenAI/edge/Reddit/trending UI. Keep red theme + light/dark.
- **Gate:** `next build` + `tsc` pass.

## Phase 10 — Config, docs, verification, morning report
- Rewrite `.env.example`, `docker-compose.yml`, `Makefile`, `docs/*` for the new stack.
- Backend import check, alembic dry-run, frontend build, grep for removed-vendor leftovers.
- Pipeline smoke test (mocked externals).
- Write `MORNING_REPORT.md`: what shipped, what's stubbed pending keys, how to test, open Qs.

---

## Cross-cutting "unkillable" guarantees
- Every external call: timeout + retry/backoff + graceful degradation when key is a placeholder.
- Idempotent Celery tasks, row-level locks for scheduling, dead-letter on repeated failure.
- All secrets/tokens encrypted at rest (Fernet). Tenant isolation enforced in every query.
- One pricing source (`pricing.md` ↔ `core/pricing.py`). One LLM/TTS/image interface each.
- No silent caps: log truncations/fallbacks; surface to user (quota fallback notice).

## Deferred (explicitly, per plan.md)
- Stripe billing (provision via admin until then).
- Final credit-number calibration (constants live, sign-off pending).
- Live API verification (keys are placeholders).
