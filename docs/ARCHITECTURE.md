# ViralFlux — Architecture Overview

---

## System Diagram

```
                         ┌───────────────────────────────────────────┐
                         │           NGINX  (Port 80 / 443)           │
                         │                                             │
                         │  /          →  Next.js frontend            │
                         │  /api/      →  FastAPI backend             │
                         │  /n8n/      →  n8n workflow UI             │
                         │  /media/    →  Static media (served local) │
                         └──────────┬──────────────┬────────┬─────────┘
                                    │              │        │
                     ┌──────────────▼───┐  ┌───────▼─────┐ │
                     │  Next.js App     │  │  FastAPI App │ │
                     │  (Port 3000)     │  │  (Port 8000) │ │
                     │  React / shadcn  │  │  Python 3.12 │ │
                     └──────────────────┘  └──────┬───────┘ │
                                                  │         │
                              ┌───────────────────┤         │
                              │                   │         │
                    ┌─────────▼──┐       ┌────────▼──┐  ┌──▼──────────┐
                    │ PostgreSQL  │       │   Redis   │  │  n8n Engine │
                    │  Port 5432  │       │  Port 6379│  │  Port 5678  │
                    │  (App data) │       │(Cache/MQ) │  │  (Workflows)│
                    └─────────────┘       └─────┬─────┘  └─────────────┘
                                                │
                  ┌─────────────────────────────┴──────────┐
                  │                                        │
        ┌─────────▼──────────┐                  ┌──────────▼─────────┐
        │   Celery Worker     │                  │    Celery Beat      │
        │  (concurrency=2)    │                  │  (scheduler)        │
        │  queue: video,      │                  │  scan_schedules /5m │
        │         analytics   │                  │  sync_analytics /1d │
        └─────────┬───────────┘                  └─────────────────────┘
                  │
                  │  beat enqueues due jobs onto the worker queues
                  │
     ┌────────────▼──────────────────────┐
     │         Video Pipeline              │
     │                                     │
     │  Genre handler (Horror / Brainrot / │
     │                 custom)             │
     │    ↓ GeminiService (script + SEO,   │
     │        Lite / Balanced / Max tier)  │
     │    ↓ ElevenLabsService (voice.mp3 + │
     │        word timestamps)             │
     │    ↓ Horror : ImagenService (images)│
     │      Brainrot: CC0 footage library  │
     │    ↓ Captions (ElevenLabs ts → ASS, │
     │        Whisper fallback)            │
     │    ↓ FFmpegUtils (final.mp4)        │
     └────────────┬───────────────────────┘
                  │
       ┌──────────▼──────────────┐
       │   YouTube Data API v3    │
       │  direct multi-account    │
       │  OAuth (resumable upload)│
       └──────────────────────────┘
```

---

## Service Responsibilities

### Nginx
Nginx acts as the single public entry point. It terminates all HTTP(S) connections and routes traffic to the correct internal service by URL prefix. It also serves the `/media/` directory directly from the mounted volume with 30-day cache headers, avoiding any FastAPI overhead for static file delivery.

### Next.js Frontend (Port 3000)
The frontend is a Next.js 14 App Router application using shadcn/ui components with a dark red theme. It handles all user-facing pages: the public marketing site, authentication flows (register, login, OTP verify, password reset), and the protected dashboard. It communicates with the backend exclusively over `/api/` (routed through Nginx) using an Axios instance that automatically attaches Bearer tokens and handles 401 refresh cycles.

### FastAPI Backend (Port 8000)
The backend is a Python 3.12 FastAPI application providing the REST API under `/api/v1/`. It uses SQLAlchemy 2.0 with async sessions for all database access and Pydantic v2 models for validation. Authentication is JWT-based (15-minute access tokens, 7-day refresh tokens stored in an httpOnly cookie). The backend handles request validation, business logic, quota enforcement, and queuing tasks to Celery. It does not perform any long-running work itself.

### Celery Worker
The worker container runs the same Docker image as the backend but starts with the Celery command instead of Uvicorn. It processes two queues: `video` (for video generation and upload tasks) and `analytics` (for YouTube Analytics snapshots). Concurrency is set to 2 workers by default. Each video generation task can take 30–120 seconds and involves multiple external API calls.

### Celery Beat (Scheduler)
The `beat` container also runs the same image, started with `celery -A app.workers.celery_app beat`. It is the **primary, DB-driven scheduler** for the platform and is **required** for posting automation. Its two scheduled tasks live in `app/workers/celery_app.py`:
- **`scan_schedules`** — every 5 minutes; reads enabled channel schedules from the database, finds due posts, and enqueues generation tasks onto the worker.
- **`sync_analytics`** — daily; enqueues a YouTube Analytics refresh for every connected channel.

n8n cron workflows are only a thin, stateless safety-net nudge on top of beat (see `n8n/README.md`); they make no scheduling decisions of their own.

### PostgreSQL (Port 5432)
The primary data store for all application state: users, plans, channels, schedule configs, video jobs, blog posts, and analytics snapshots. n8n also stores its workflow data in a separate PostgreSQL database (`n8n`) on the same server. Data is persisted in the `postgres_data` Docker volume.

### Redis (Port 6379)
Redis serves three logical roles across separate databases: a general cache for short-lived data such as OTP codes (DB 0, TTL 15 minutes), the Celery message broker (DB 1), and the Celery result backend (DB 2). There is no longer any trending-topics cache (Reddit/trend discovery was removed).

### n8n (Port 5678)
n8n is a **thin, supplementary** automation layer — **not** the scheduler. The primary scheduler is Celery `beat` (above). n8n runs four stateless workflows that only call backend endpoints over the Docker network (`http://backend:8000/api/v1/...`): `scheduled_posting` (nudges the backend to scan schedules), `approval_reminder` (nudges the backend to send approval reminders), `analytics_sync` (nudges the daily analytics refresh), and `video_generation_trigger` (an inbound webhook that delegates a single job to the backend). Workflows hold no tenant state and make no per-tenant decisions; all logic lives in the backend. The old `trend_discovery` workflow was removed with Reddit. See `n8n/README.md`.

---

## Video Generation Pipeline — Step by Step

This is the full lifecycle of a single video job from trigger to YouTube.

**Step 1 — Job Creation**
A user clicks "Generate Video" in the dashboard, or the `scan_schedules` beat task finds a due schedule. The FastAPI `/videos/generate` endpoint (or the beat task) first **debits the user's credit balance** for the requested duration × model tier (see `pricing.md`), then creates a `VideoJob` record with `status=queued` and enqueues a `generate_video` Celery task. If the user lacks credits the request is rejected with `402 Payment Required`.

**Step 2 — Task Pickup**
The Celery worker picks up the task from the `video` queue. It loads the job and channel records from the database and immediately sets `status=generating`.

**Step 3 — Genre Dispatch**
The worker resolves the genre handler using the channel's genre (`horror`, `brainrot`, or a Pro/Agency `custom` genre). The handler is invoked with the topic and channel configuration (ElevenLabs voice ID, music bucket, model tier).

**Step 4 — Script + SEO Generation (Gemini)**
A single LLM provider — **Gemini only** — generates both the narration script and the SEO metadata, using the model tier the user selected (Lite / Balanced / Max, mapped to the `GEMINI_MODEL_*` env vars). The script is trimmed to the plan's character budget (`DURATION_CHARS` in `pricing.md`, ~15 chars/sec). SEO output (`title`, `description`, `tags`, `hashtags`) is returned as structured JSON. There is no second LLM and no Reddit story scraping — topics come from the user, the channel's topic queue, or a Gemini suggestion.

**Step 5 — Voice Synthesis (ElevenLabs)**
`ElevenLabsService` synthesizes the script to `voice.mp3` using the channel's voice ID and the `ELEVENLABS_MODEL` (default `eleven_flash_v2_5`). It also returns **word-level timestamps** in the same call, which feed caption generation. ElevenLabs is the only TTS provider — Google Cloud TTS and edge-tts have been removed.

**Step 6 — Visuals (genre-dependent)**
- **Horror** → `ImagenService` generates atmospheric images with Imagen 4 Fast (`IMAGEN_MODEL`) from prompts derived from the script, sized to 1080x1920.
- **Brainrot** → the worker pulls a clip from the self-hosted CC0 **footage** library (`assets/footage/<bucket>/`, buckets: `satisfying`, `parkour_clean`, `hydraulic`, `kinetic_sand`), randomized to avoid repetition. No stock-image vendor (Pexels/Pixabay/Unsplash) is used.

**Step 7 — Caption Generation**
Captions are built primarily from the ElevenLabs word timestamps (Step 5) rendered to an ASS subtitle file. If timestamps are unavailable, `faster-whisper` transcribes `voice.mp3` locally (no API call) using the configured Whisper model (default: `base`) as a fallback.

**Step 8 — Video Assembly (FFmpeg)**
`FFmpegUtils` assembles the final video. For **Horror** (image-based):
1. Apply Ken Burns zoom effect to each image (slow 1.0x→1.05x zoom over 5 seconds) producing short clips
2. Concatenate clips with xfade crossfade transitions (0.5s fade between each image)

For **Brainrot** (footage-based) the selected CC0 clip is looped/trimmed to the narration length and its own audio dropped. Both genres then share:

3. Mix audio: voice at full volume + background CC0 music at 15% volume (amix filter)
4. Burn-in captions from the ASS file (bottom-center, high-contrast outline)

Output: `final.mp4` at 1080x1920, 30fps, H.264/AAC.

**Step 9 — Approval Routing**
The video path is saved to the job record and `status` is set to `pending_approval`. If the channel schedule has `require_approval=True` and an `approval_email` is set, a Resend email is sent with a one-click approve link. If `require_approval=False`, the job is automatically approved and the `upload_to_youtube` task is queued immediately.

**Step 10 — YouTube Upload (direct multi-account OAuth)**
The `upload_to_youtube` Celery task decrypts the channel's stored OAuth tokens (each connected YouTube account holds its own encrypted tokens), refreshes them if expired, and uses the YouTube Data API v3 resumable upload endpoint **directly** — PostProxy has been removed. It sets the title, description, tags, category (22 = People & Blogs), and `privacyStatus`. If `scheduled_for` is set, it passes `scheduledStartTime` to schedule the publication. On success, `status=posted`, `youtube_video_id`, and `youtube_url` are persisted.

**Step 11 — Analytics Sync**
The daily `sync_analytics` beat task (not n8n) calls the YouTube Analytics API for each posted video and stores a snapshot in `video_analytics` (views, likes, comments, watch time hours).

---

## Database Design Rationale

**UUID primary keys everywhere:** All tables use UUIDs (`gen_random_uuid()`) rather than auto-incrementing integers. This prevents ID enumeration attacks and allows the frontend to generate IDs optimistically before server confirmation.

**Soft-delete on channels:** `youtube_channels.is_active = False` rather than hard deletes. This preserves referential integrity since `video_jobs` references channels and historical analytics data should remain queryable.

**OAuth tokens encrypted at rest:** `oauth_access_token` and `oauth_refresh_token` are stored as AES-encrypted ciphertext in the database. The `ENCRYPTION_KEY` env var holds the 32-byte Fernet key. Token decryption happens only inside Celery tasks immediately before API calls.

**`video_jobs.seo_tags` as `TEXT[]`:** PostgreSQL native array type is used rather than a JSON column or a separate join table. This allows direct array operations (`ANY`, `@>`) without JSON parsing overhead, though ViralFlux currently only reads the full array.

**`channel_schedules` as 1:1 to channels:** Rather than embedding schedule fields directly in `youtube_channels`, scheduling config lives in a separate `channel_schedules` table. This keeps the channel record clean and allows schedule to be null (not configured yet) without nullable columns everywhere.

**`plans.features` as JSONB:** Plan features are stored as a JSONB column rather than individual boolean columns. This allows new features to be added to plans without schema migrations.

---

## Genres (replacing the old format list)

Content is organized into **genres** rather than the old open-ended "format" plugin list. There are three:

| Genre | Visuals | Music bucket(s) | Availability |
|---|---|---|---|
| **Horror** | Imagen 4 Fast images | `horror_ambient` | All plans (Free: Horror *or* Brainrot) |
| **Brainrot** | self-hosted CC0 footage loops | `upbeat_hype` | Starter+ (Free can pick instead of Horror) |
| **Custom** | per channel, user-defined prompt/style | configurable | Pro & Agency |

The genre drives which visual path the pipeline takes (Imagen vs. footage library), the default music bucket, and the prompt style. Genre availability per plan is enforced by the credits/plan layer — see `pricing.md`.

See [FORMATS.md](./FORMATS.md) for the genre handler contract and a worked example.

---

## Single-LLM (Gemini-only), 3-Tier Strategy

ViralFlux uses **one** LLM provider — Google **Gemini** — for everything: script writing, SEO metadata, and any topic suggestion. The old second provider (OpenAI/GPT) has been removed. Gemini's structured-output mode produces the parseable JSON needed for tag/hashtag arrays, so a separate "analytical" model is unnecessary.

Three tiers are exposed to users — **Lite / Balanced / Max** — each mapped to an env-configurable Gemini model so the underlying model can be swapped without code changes:

| UI tier | Env var | Default | Multiplier (credits) |
|---|---|---|---|
| Lite | `GEMINI_MODEL_LITE` | `gemini-3.1-flash-lite` | ×0.7 |
| Balanced | `GEMINI_MODEL_BALANCED` | `gemini-3.1-flash` | ×0.85 |
| Max | `GEMINI_MODEL_MAX` | `gemini-3.5-flash` | ×1.0 |

Tier availability is governed by plan and the monthly **Max Quota** (see `pricing.md`). Real model IDs are never exposed to users.

---

## Cost Breakdown Per Video

The real variable cost is dominated by **voice + images**, both driven by duration; the LLM tier is negligible (<$0.01). Users are billed in **credits**, not dollars — see `pricing.md` for the credit math and margins.

| Component | Provider | Approx. Cost |
|---|---|---|
| Script + SEO (Gemini, any tier) | Google AI | <$0.01 |
| Voice (ElevenLabs `eleven_flash_v2_5`, ~900 chars) | ElevenLabs | ~$0.09 ($103 / 1M chars) |
| Images (Horror, Imagen 4 Fast) | Google AI | ~$0.005–$0.02 / image |
| Footage (Brainrot, self-hosted CC0) | local | $0.00 |
| Music (self-hosted CC0) | local | $0.00 |
| Captions (ElevenLabs timestamps / Whisper fallback) | local | $0.00 |
| Video assembly (FFmpeg) | local | $0.00 |
| YouTube upload (direct OAuth) | YouTube Data API | $0.00 |

The dashboard shows the **credit cost** on every generation, computed from `credits_for_video(duration, model)` in `backend/app/core/pricing.py` (the single source of truth mirrored from `pricing.md`).
