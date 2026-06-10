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
                                    ┌───────────▼──────────────┐
                                    │      Celery Worker        │
                                    │  (concurrency=2)          │
                                    │  queue: video, analytics  │
                                    └───────────┬───────────────┘
                                                │
                               ┌────────────────▼──────────────────┐
                               │         Video Pipeline              │
                               │                                     │
                               │  Format Plugin (e.g. HorrorStory)  │
                               │    ↓ GeminiService (script)        │
                               │    ↓ OpenAIService (SEO)           │
                               │    ↓ TTSService (voice.mp3)        │
                               │    ↓ PexelsService (images)        │
                               │    ↓ Whisper (captions.srt)        │
                               │    ↓ FFmpegUtils (final.mp4)       │
                               └───────────────────────────────────┘
                                                │
                                    ┌───────────▼──────────────┐
                                    │   YouTube Data API v3     │
                                    │   (resumable upload)      │
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

### PostgreSQL (Port 5432)
The primary data store for all application state: users, plans, channels, schedule configs, video jobs, blog posts, and analytics snapshots. n8n also stores its workflow data in a separate PostgreSQL database (`n8n`) on the same server. Data is persisted in the `postgres_data` Docker volume.

### Redis (Port 6379)
Redis serves two purposes: it is the Celery message broker (database 0) and result backend (database 1), and it is used as a cache for short-lived data like OTP codes (TTL 15 minutes) and the AI trending topics cache (refreshed daily by n8n).

### n8n (Port 5678)
n8n provides the scheduling and automation layer. It runs five persistent workflows: scheduled posting trigger, trend discovery, approval reminders, analytics sync, and a webhook receiver for job completion signals. n8n calls the FastAPI internal endpoints using Docker service-name URLs (`http://backend:8000/api/v1/...`).

---

## Video Generation Pipeline — Step by Step

This is the full lifecycle of a single video job from trigger to YouTube.

**Step 1 — Job Creation**
A user clicks "Generate Video" in the dashboard (or n8n fires the scheduled posting workflow). The FastAPI `/videos/generate` endpoint creates a `VideoJob` record with `status=queued` and enqueues a `generate_video` Celery task.

**Step 2 — Task Pickup**
The Celery worker picks up the task from the `video` queue. It loads the job and channel records from the database and immediately sets `status=generating`.

**Step 3 — Format Plugin Dispatch**
The worker resolves the format plugin from the format registry using `job.format_slug` (e.g., `horror_story`). The plugin's `prepare()` method is called with the topic and channel configuration (voice provider, voice ID, music category).

**Step 4 — Script Generation (Gemini)**
The `HorrorStoryPlugin` calls `GeminiService.generate_script()`. Gemini Flash receives a structured prompt with the topic or scraped Reddit story text and returns a JSON object containing `script_text` (max 160 words), `hook_line` (opening sentence), and `estimated_duration_sec` (45–58 seconds).

**Step 5 — SEO Generation (GPT-4o-mini)**
The plugin calls `OpenAIService.generate_seo()` with the generated script and topic. GPT-4o-mini returns structured JSON with `title` (max 70 chars), `description` (max 300 chars), 15 `tags`, 5 `hashtags`, and `thumbnail_text`. The `response_format={"type":"json_object"}` parameter enforces clean JSON output.

**Step 6 — Voice Synthesis (TTS)**
The TTS service configured for the channel synthesizes the script to `voice.mp3`. Provider priority: ElevenLabs (highest quality, ~$0.003/video) → Google Cloud TTS → edge-tts (free). The `TTSService` base class enforces a `synthesize(text, voice_id, output_path)` interface, making providers interchangeable.

**Step 7 — Image Sourcing (Pexels)**
The `PexelsService` extracts the top 5 nouns from the script and searches Pexels for atmospheric images using queries like `"{noun} dark horror atmospheric"`. Images are downloaded to the job's temp directory and resized to 1080x1920 (9:16 portrait) using FFmpeg's scale-then-crop filter.

**Step 8 — Caption Generation (Whisper)**
`faster-whisper` transcribes `voice.mp3` locally (no API call) using the configured Whisper model (default: `base`). Word-level timestamps are extracted and written to `captions.srt`.

**Step 9 — Video Assembly (FFmpeg)**
`FFmpegUtils` assembles the final video in four sub-steps:
1. Apply Ken Burns zoom effect to each image (slow 1.0x→1.05x zoom over 5 seconds) producing short clips
2. Concatenate clips with xfade crossfade transitions (0.5s fade between each image)
3. Mix audio: voice at full volume + background music at 15% volume (amix filter)
4. Burn-in captions from the SRT file (Arial Bold 48pt, white text with black outline, bottom 25% of frame)

Output: `final.mp4` at 1080x1920, 30fps, H.264/AAC.

**Step 10 — Approval Routing**
The video path is saved to the job record and `status` is set to `pending_approval`. If the channel schedule has `require_approval=True` and an `approval_email` is set, an email is sent with a one-click approve link. If `require_approval=False`, the job is automatically approved and the `upload_to_youtube` task is queued immediately.

**Step 11 — YouTube Upload**
The `upload_to_youtube` Celery task decrypts the stored OAuth tokens, refreshes them if expired, and uses the YouTube Data API v3 resumable upload endpoint to push the video. It sets the title, description, tags, category (22 = People & Blogs), and `privacyStatus`. If `scheduled_for` is set, it passes `scheduledStartTime` to schedule the publication. On success, `status=posted`, `youtube_video_id`, and `youtube_url` are persisted.

**Step 12 — Analytics Sync**
A daily n8n workflow calls the YouTube Analytics API for each posted video and stores a snapshot in `video_analytics` (views, likes, comments, watch time hours).

---

## Database Design Rationale

**UUID primary keys everywhere:** All tables use UUIDs (`gen_random_uuid()`) rather than auto-incrementing integers. This prevents ID enumeration attacks and allows the frontend to generate IDs optimistically before server confirmation.

**Soft-delete on channels:** `youtube_channels.is_active = False` rather than hard deletes. This preserves referential integrity since `video_jobs` references channels and historical analytics data should remain queryable.

**OAuth tokens encrypted at rest:** `oauth_access_token` and `oauth_refresh_token` are stored as AES-encrypted ciphertext in the database. The `ENCRYPTION_KEY` env var holds the 32-byte Fernet key. Token decryption happens only inside Celery tasks immediately before API calls.

**`video_jobs.seo_tags` as `TEXT[]`:** PostgreSQL native array type is used rather than a JSON column or a separate join table. This allows direct array operations (`ANY`, `@>`) without JSON parsing overhead, though ViralFlux currently only reads the full array.

**`channel_schedules` as 1:1 to channels:** Rather than embedding schedule fields directly in `youtube_channels`, scheduling config lives in a separate `channel_schedules` table. This keeps the channel record clean and allows schedule to be null (not configured yet) without nullable columns everywhere.

**`plans.features` as JSONB:** Plan features are stored as a JSONB column rather than individual boolean columns. This allows new features to be added to plans without schema migrations.

---

## Format Plugin Pattern

The `FormatPlugin` abstract base class (at `backend/app/services/formats/base.py`) defines the contract that every content format must implement. Adding a new format requires only creating a new plugin file — zero changes to the Celery task, pipeline, or API.

The registry maps `format_slug` strings (e.g., `horror_story`) to plugin class instances. When the Celery worker processes a job, it calls `get_format_plugin(job.format_slug)` to resolve the correct plugin.

Each plugin implements:
- `prepare(topic, channel_config)` — runs LLM calls and returns a `FormatOutput` dataclass containing `script`, `seo_title`, `seo_description`, `seo_tags`, `voice_provider`, `voice_id`, and `cost_estimate_usd`
- `get_pipeline_steps()` — returns the list of `VideoPipeline` step names this format requires (e.g., `["images", "tts", "captions", "assemble"]`)
- `get_music_category()` — returns the default music category slug for this format
- `min_plan` — the minimum subscription plan required to use this format

The `VideoPipeline` class reads the step list from the plugin and only executes the relevant steps, making it easy to build formats that skip certain stages (e.g., a text-only format that skips image sourcing).

See [FORMATS.md](./FORMATS.md) for full plugin documentation and a worked example.

---

## Two-LLM Strategy Rationale

ViralFlux uses two separate LLM providers with different strengths for different tasks.

**Gemini Flash 2.5 Lite (Google AI) — Creative tasks**

Gemini is used for story writing, script generation, and topic virality analysis. It excels at long-form creative generation with vivid, evocative prose. The `flash-lite` variant is the cheapest available model at approximately $0.000075 per 1,000 input tokens. At script lengths of ~200–400 tokens in + ~300 tokens out, Gemini costs approximately $0.0005 per script generation.

Temperature is set to 0.85 for scripts (high creativity) and 0.4 for topic picking (more deterministic).

**GPT-4o-mini (OpenAI) — Analytical tasks**

OpenAI is used for SEO metadata generation and analytics-based decisions. GPT-4o-mini enforces the `response_format={"type":"json_object"}` parameter which guarantees parseable JSON output — critical for structured data like tag arrays that must not have markdown wrappers. GPT-4o-mini also follows structured formatting instructions more reliably than Gemini for analytical tasks. Cost is approximately $0.00015 per 1,000 input tokens.

**Total LLM cost per video: $0.001–$0.003**

Neither model is used for anything the other model handles. If you want to swap providers, replace the `GeminiService` or `OpenAIService` with any class that implements `LLMService` from `base.py`.

---

## Cost Breakdown Per Video

| Component | Provider | Approx. Cost |
|---|---|---|
| Script generation | Gemini Flash 2.5 Lite | ~$0.0005 |
| SEO generation | GPT-4o-mini | ~$0.0008 |
| Voice (edge-tts, free tier) | Microsoft Azure (free) | $0.00 |
| Voice (ElevenLabs, ~900 chars) | ElevenLabs | ~$0.003 |
| Voice (Google Cloud TTS WaveNet) | Google Cloud | ~$0.0004 |
| Images (Pexels API) | Pexels | $0.00 (free API) |
| Caption generation (Whisper) | Self-hosted (local) | $0.00 |
| Video assembly (FFmpeg) | Self-hosted (local) | $0.00 |
| YouTube upload | YouTube Data API | $0.00 |
| **Total — free voice (edge-tts)** | | **~$0.002** |
| **Total — ElevenLabs voice** | | **~$0.005** |
| **Total — Google Cloud TTS** | | **~$0.002** |

At 100 videos/month with ElevenLabs voice: total LLM + TTS cost is approximately **$0.50**. This is the real variable cost of the product — server costs are fixed.

The dashboard shows `cost_usd` on every video card so users can track spend.
