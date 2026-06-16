# ViralFlux v2 — Morning Report

**Built overnight 2026-06-16, fully autonomous.** Every phase in `IMPLEMENTATION_PLAN.md` is done.
The whole stack boots, migrates, seeds, and serves — verified live in Docker (see §Verification).

---

## TL;DR
The pivot in your `plan.md` is fully implemented and running:
- ❌ Removed completely (code, deps, config, UI, n8n): **OpenAI, Reddit/PRAW, PostProxy, edge-tts, Google TTS, Pexels/Pixabay/Unsplash**.
- ✅ **Gemini-only** LLM with 3 tiers (Lite/Balanced/Max), env-configurable model IDs.
- ✅ **ElevenLabs-only** TTS (`eleven_flash_v2_5`), genre voice settings, word-level timestamps, community-voice hooks.
- ✅ **Multi-tenant**: account → many channels (per plan) → per-channel genre, voice, schedule, weekly seed prompt. Workspace-style **channel switcher** in the top bar.
- ✅ **Direct multi-account YouTube OAuth** (our own app; one user can connect channels under different Google accounts). PostProxy gone.
- ✅ **Genres**: Horror (Imagen images + ken-burns), Brainrot (CC0 loop footage), Custom. Manual-script OR AI-from-seed per short.
- ✅ **Credits system**: wallet + ledger + Max-quota→Balanced fallback + top-ups + add-ons. Full pricing in `pricing.md` ↔ `backend/app/core/pricing.py`.
- ✅ **Captions**: ElevenLabs word timestamps → ASS → FFmpeg burn (Whisper fallback).
- ✅ **Scheduler**: DB-driven Celery **beat** (`scan_schedules`, tenant-safe row locks), n8n demoted to a stateless supplementary automator.

> Per your instruction, **final credit-number calibration is deferred** — the numbers are live in code but isolated in one module for a one-line tweak when you sign off. **Stripe is deferred** (top-ups/upgrades provision immediately via admin/endpoint for now).

---

## Verification (run live tonight, not just static)
- **Whole app imports** inside the container: `import app.main` → OK (every router/service/model/task resolves).
- **Backend byte-compiles** end to end; zero stale references to any removed vendor.
- **Fresh Alembic migration** `001` builds the full v2 schema on a clean DB.
- **Seed** creates plans **free/starter/pro/agency** (credits 30/850/2600/8000, Max quota 0/0/30/120, channels 1/2/5/15) and genres **horror/brainrot/custom**.
- **All 8 containers up**: postgres, redis, backend, worker, beat, frontend, n8n, nginx.
- `GET /health` → `{"status":"ok"}`. `GET /api/v1/plans/` returns the new plans w/ full feature blobs through the live API.
- **Worker** registered: `generate_video`, `upload_to_youtube`, `sync_analytics`, `scan_schedules`. **Beat** running.
- **Frontend** `npm run build` → clean, 20 routes, type-checked.

### The stack is RUNNING right now
```bash
docker compose ps          # all up
# Frontend:  http://localhost        (via nginx)  or http://localhost:3000
# API docs:  http://localhost:8000/docs
# n8n:       http://localhost:5678
docker compose logs -f backend worker beat
docker compose down        # stop   |   docker compose up -d   # start
```

---

## What's stubbed pending real API keys (by design — you chose placeholders)
Everything is wired to work the instant real keys land in `.env`. With placeholder keys, the
external calls raise a clear error instead of running; the app, DB, auth, credits, scheduling,
and UI all function. To go live, fill in:
- `GOOGLE_AI_API_KEY` (Gemini scripts/SEO **and** Imagen images — one key).
- `ELEVENLABS_API_KEY` (TTS + word timestamps + voice library).
- `YOUTUBE_CLIENT_ID` / `YOUTUBE_CLIENT_SECRET` (your OAuth app; redirect URI already set to `/api/v1/channels/youtube/callback`).
- `ENCRYPTION_KEY` — currently empty (derives a stable key from `APP_SECRET_KEY`). For prod set a real Fernet key (command in `.env`).
- `RESEND_API_KEY` is already real (kept from before).

### Model IDs note
`GEMINI_MODEL_LITE/BALANCED/MAX` default to `gemini-3.1-flash-lite / 3.1-flash / 3.5-flash`
(the names from your `plan.md`). These are **env vars** — if the live Gemini model IDs differ,
change them in `.env` only; no code change. Same for `IMAGEN_MODEL`.

### Asset libraries (need content dropped in, $0 ongoing)
- Music: `assets/music/<bucket>/` — run `scripts/seed_music.sh`, then add CC0 tracks.
- Brainrot footage: `assets/footage/<bucket>/` — run `scripts/seed_footage.sh`, then add CC0 loops.
Both rotate randomly per video; empty = pipeline proceeds without that layer.

---

## Open questions for you
1. **Final credit calibration** — say the word and I'll lock the numbers (they're in `pricing.md`).
2. **Gemini/Imagen real model IDs** — confirm the exact IDs when you have them so I set the env defaults.
3. **Stripe** — when you're ready I'll wire checkout for subscriptions + top-ups + add-ons (schema + endpoints already exist).
4. **Custom genre** prompt templates — currently Custom reuses the generated-image path; tell me the creative direction you want for it.

---

## Where things live
- Plan/economics: `pricing.md`, `IMPLEMENTATION_PLAN.md`, `backend/app/core/pricing.py`.
- Genres/voices: `backend/app/core/genres.py`.
- Services: `backend/app/services/{llm,tts,assets,video,formats}/`, `youtube_service.py`, `credit_service.py`.
- Pipeline/workers: `backend/app/services/video/pipeline.py`, `backend/app/workers/`.
- Frontend: `frontend/src/` (channel switcher, generate flow, `/dashboard/billing`, new pricing page).
- Docs updated: `docs/{ARCHITECTURE,SETUP,API,FORMATS,DEPLOYMENT}.md`, `n8n/README.md`.

The work is checkpointed on branch **`feat/viralflux-v2-rearchitecture`** (not pushed) for your review.
