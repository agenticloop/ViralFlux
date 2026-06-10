# ViralFlux — YouTube Shorts Automation SaaS
## Master Build Plan v1.0
### For Claude Code — End-to-End Build Instructions

---

## 0. Client Vision (From Meeting Notes)

> *"I want an automated YouTube reel generator... it automatically, like our scheduler for LinkedIn and Instagram works with our social media manager, I was wondering we can transition that over and modify that so it can do that for YouTube reels, while keeping costs down from having one reel not costing more than one to three dollars."*
> — Sunny Singh

> *"The main thing is to have our cost, ideally under $1... it's only going to be doing text generation, and then we can just use a Python package to do the stitching, the captions, and everything would all come from the voice."*
> — Sunny Singh

> *"The main thing is the story... if I am watching any video, I will not focus more on pictures or is it a video or what it is, but I will hear that story. If it is interesting, then I will continue."*
> — Aisha Rahib (summarizing Sunny's vision)

> *"If it can be a full on AI manager — a full YouTube AI manager that can be self-autonomous — then that's perfect. An AI can make the choices onto what type of content it wants to make for that channel or for any channel."*
> — Sunny Singh

**Core Constraints from Client:**
- Cost per short: **under $1, target $0.02–$0.10**
- Story/voiceover is the product — visuals are secondary
- Must post directly to YouTube end-to-end
- Must support multiple channels with distinct identities (per-channel voice)
- AI should manage itself: pick trends, decide format, suggest new channels

---

## 1. Product Name & Branding

- **Product Name:** ViralFlux
- **Tagline:** "Automate your YouTube Shorts empire."
- **Primary Color:** Red (`#E5192A` primary, `#FF3040` accent)
- **Secondary:** Dark gray `#0F0F0F`, white `#FAFAFA`
- **Font:** Inter (headings bold, body regular)
- **Theme:** Dark mode default, light mode toggle available

---

## 2. Tech Stack

### Backend
| Layer | Technology |
|---|---|
| API Framework | FastAPI (Python 3.12) |
| Database | PostgreSQL 16 |
| ORM | SQLAlchemy 2.0 + Alembic migrations |
| Task Queue | Celery 5 + Redis |
| Cache | Redis 7 |
| Auth | JWT (python-jose) + SMTP email verification |
| Video Processing | FFmpeg (via subprocess + ffmpeg-python) |
| File Storage | Local `/media/` volume (S3-ready interface) |

### LLMs (Two-LLM Strategy)
| Role | Model | Purpose |
|---|---|---|
| **Primary — Creative** | Google Gemini Flash 2.5 Lite | Script writing, story generation, creative content, dialogue |
| **Secondary — Analytical** | OpenAI GPT-4o-mini | SEO titles/tags/descriptions, trend analysis, channel strategy decisions |

**Why two LLMs:**
- Gemini Flash Lite = cheapest possible creative generation (~$0.000075/1K tokens)
- GPT-4o-mini = best structured JSON output for SEO + analytics (~$0.00015/1K tokens)
- Total LLM cost per video: **~$0.003–$0.008**

### Frontend
| Layer | Technology |
|---|---|
| Framework | Next.js 14 (App Router) |
| UI Components | shadcn/ui |
| Styling | Tailwind CSS (red theme) |
| State | Zustand |
| Data Fetching | TanStack Query (React Query) |
| Forms | React Hook Form + Zod |
| Charts | Recharts |
| Icons | Lucide React |
| Dark Mode | next-themes |

### Infrastructure
| Service | Technology |
|---|---|
| Reverse Proxy | Nginx |
| Workflow Engine | n8n (self-hosted) |
| Containerization | Docker Compose |
| Environment | Single centralized `.env` file |

---

## 3. System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         NGINX (Port 80/443)                         │
│   /          → Next.js frontend                                     │
│   /api/      → FastAPI backend                                      │
│   /n8n/      → n8n workflow UI                                      │
└────────────┬───────────────────┬──────────────────────────────────┘
             │                   │                    │
    ┌────────▼──────┐   ┌────────▼──────┐   ┌────────▼──────┐
    │  Next.js App  │   │  FastAPI App  │   │   n8n Engine  │
    │  (Port 3000)  │   │  (Port 8000)  │   │  (Port 5678)  │
    └───────────────┘   └───────┬───────┘   └───────┬───────┘
                                │                    │
                    ┌───────────┼────────────────────┘
                    │           │
           ┌────────▼──┐  ┌────▼──────┐  ┌────────────┐
           │ PostgreSQL │  │   Redis   │  │   Celery   │
           │  (DB+Data) │  │(Cache+MQ) │  │  Workers   │
           └────────────┘  └───────────┘  └─────┬──────┘
                                                 │
                                    ┌────────────▼───────────────┐
                                    │      FFmpeg Video Pipeline  │
                                    │  Script → TTS → Images →   │
                                    │  Stitch → Captions → MP4   │
                                    └────────────────────────────┘
```

---

## 4. Content Formats

### ACTIVE — Phase 1 (Build Now)

#### Format 1: Horror Story Shorts
> *Sunny's words: "I've made this reel myself... it's like a horror story reel, based off of Reddit creepypastas."*

- **Source:** Reddit r/nosleep, r/creepypasta, r/LetsNotMeet scraped via Reddit API
- **Script:** Gemini Flash rewrites/adapts story to 45–60 sec narration
- **Visuals:** 5–6 static images fetched from Pexels/Pixabay (dark, atmospheric)
- **Voice:** Deep dramatic male (ElevenLabs "Adam" or Google TTS WaveNet-D)
- **Music:** Ambient horror background track (local curated library)
- **Captions:** Word-by-word burn-in via FFmpeg + Whisper timestamps
- **Layout:** Full-screen image with caption overlay at bottom 30%
- **Cost:** ~$0.02–$0.08 per video

---

### PLANNED — Phase 2 (Architecture Ready, Build Later)

#### Format 2: Brainrot Dialogue
> *"The videos that are getting a lot of traction are pretty brain rot... cheap animation, cheap everything, and it has around 2.5 million views."*

- Two AI character voices debating/reacting (Obama vs Jordan Peterson style)
- Minecraft / GTA / Subway Surfers gameplay loop in background (bottom 50%)
- Character avatars top 50%
- Speechify or ElevenLabs voice clones

#### Format 3: Ranking / Listicle
- "Top 5 [X]" format
- 5 stitched stock video clips (one per item, ~8s each)
- GPT-4o-mini generates ranked list, Gemini writes hook script
- Upbeat music

#### Format 4: Motivational / Stoic Quotes
- Single dramatic background video loop
- Deep voice reading quote
- Text animation overlay

#### Format 5: Pre-Existing Clip Stitch
> *"They use pre-existing ranking videos, the current competition on the YouTube reels, and then they'll just stitch them together."*

- AI picks 5 trending clips from curated sources
- Adds commentary voiceover on top
- Auto-reframe to 9:16 via FFmpeg

**NOTE: The format system must be built modular from day 1. Each format is a plugin (`FormatPlugin` base class) with its own pipeline steps. Adding Format 2–5 later should only require adding a new plugin file — zero changes to core.**

---

## 5. Video Generation Pipeline (Format 1 — Horror Story)

```
[TRIGGER: Manual push OR n8n schedule]
            │
            ▼
[Step 1 — Topic Selection]
  Gemini Flash: Analyze r/nosleep trending posts
  → Pick 3 candidate stories, score by virality signals
  → GPT-4o-mini: Pick best one, return JSON {title, reddit_url, raw_text}
            │
            ▼
[Step 2 — Script Generation]
  Gemini Flash: Rewrite story as 50–65 second narration script
  → Max 160 words, punchy sentences, hooks at 0s and 15s
  → Output: {script_text, estimated_duration_sec, hook_line}
            │
            ▼
[Step 3 — SEO Package]
  GPT-4o-mini: Generate YouTube metadata
  → {title (max 70 chars), description (300 chars), tags: string[15],
     hashtags: string[5], thumbnail_text}
            │
            ▼
[Step 4 — Voice Generation]
  TTS service (configured per channel):
  → ElevenLabs API → horror voice → /tmp/{job_id}/voice.mp3
  → OR Google Cloud TTS (fallback)
  → OR edge-tts (free fallback)
            │
            ▼
[Step 5 — Image Sourcing]
  Search Pexels API with story keywords
  → Download 5 atmospheric images to /tmp/{job_id}/img_0.jpg … img_4.jpg
  → Fallback: Pixabay → Unsplash
            │
            ▼
[Step 6 — Caption Generation]
  Whisper (local, whisper.cpp or faster-whisper) transcribes voice.mp3
  → Word-level timestamps → SRT file /tmp/{job_id}/captions.srt
            │
            ▼
[Step 7 — Video Assembly (FFmpeg)]
  - Resize all images to 1080x1920 (9:16)
  - Ken Burns zoom effect on each image (5s per image)
  - Crossfade transition between images (0.5s)
  - Overlay voice.mp3 as primary audio
  - Mix horror music track at 15% volume (from /assets/music/)
  - Burn captions: white text, black outline, bottom 25% of frame
  - Output: /tmp/{job_id}/final.mp4
            │
            ▼
[Step 8 — Preview & Approval]
  - Store final.mp4 in /media/previews/{job_id}.mp4
  - Update DB job status → "pending_approval"
  - If approval_required=True: send email to user with approve/reject link
  - If approval_required=False: auto-proceed to Step 9
            │
            ▼
[Step 9 — YouTube Upload]
  YouTube Data API v3:
  → resumable upload final.mp4
  → Set title, description, tags, category=22, privacyStatus=public
  → scheduledStartTime if scheduled
  → Log: video_id, url, upload_time to DB
            │
            ▼
[Step 10 — Analytics Log]
  Store in DB: job_id, channel_id, cost_usd, duration_sec,
  video_url, youtube_video_id, posted_at
  Update Google Sheet log (optional, via n8n)
```

---

## 6. Voice Recommendations

### Per-Format Voice Guide

| Format | Recommended Voice | API | Cost/video | Character |
|---|---|---|---|---|
| Horror Story | ElevenLabs "Adam" or "Arnold" | ElevenLabs | ~$0.003 | Deep, slow, dramatic |
| Brainrot | ElevenLabs custom clone | ElevenLabs | ~$0.005 | Character-specific |
| Motivational | Google TTS en-US-Neural2-D | Google Cloud TTS | ~$0.0004 | Strong, confident |
| Ranking/Facts | edge-tts "en-US-GuyNeural" | Free | $0 | Clear, neutral male |
| Female variant | edge-tts "en-US-JennyNeural" | Free | $0 | Clear, warm female |

### Voice API Options (Configured per channel)

| Provider | Quality | Cost | Notes |
|---|---|---|---|
| **ElevenLabs** | ⭐⭐⭐⭐⭐ | $0.0002/char (~$0.003/video) | Best quality, 30k chars free/mo |
| **Google Cloud TTS** | ⭐⭐⭐⭐ | $4/1M chars (~$0.0004/video) | WaveNet voices, very cheap at scale |
| **OpenAI TTS** | ⭐⭐⭐⭐⭐ | $15/1M chars (~$0.0015/video) | Alloy/Nova/Shimmer voices |
| **edge-tts** | ⭐⭐⭐ | FREE | Microsoft Azure voices, no API key |
| **Coqui TTS** | ⭐⭐⭐ | FREE (self-hosted) | Open source, runs in Docker |

**Recommendation:** Default to edge-tts (free) for Starter plan users. ElevenLabs for Pro/Agency. Allow per-channel override.

---

## 7. Media Assets Strategy

### Stock Images
| Source | API | Limit | Quality |
|---|---|---|---|
| Pexels | Free API | 200 req/hour | ⭐⭐⭐⭐⭐ |
| Pixabay | Free API | 100 req/min | ⭐⭐⭐⭐ |
| Unsplash | Free API | 50 req/hour | ⭐⭐⭐⭐⭐ |
| AI Generated | Stability AI SD3 | $0.04/image | On demand (future) |

**Search Strategy:** Extract top 5 nouns from script → search "{noun} dark atmospheric horror 4k" → download, resize to 1080x1920

### Background Music Library
- Curate 50–100 tracks stored locally in `/assets/music/`
- Categories: horror_ambient, horror_tense, upbeat_hype, cinematic_epic, lo_fi_chill
- Sources: YouTube Audio Library, Pixabay Music, Freesound.org (all CC0/royalty-free)
- New tracks added monthly — no per-video API cost
- Per-channel default genre configured in dashboard

### Background Videos (For Future Brainrot Format)
- Local library: 20 x 30-second clips in `/assets/gameplay/`
- Sources: Minecraft parkour, Subway Surfers, GTA driving (royalty-free compilations)
- FFmpeg randomly samples a 60s segment per video
- Pexels Video API as fallback

---

## 8. Pricing Plans

> Based on Sunny's model: cost must stay minimal, channel volume is the value driver.

### Plan 1 — Starter · $29/month
- **20 Shorts/month**
- **1 YouTube Channel**
- Horror Story format only
- edge-tts voice (free tier)
- Pexels/Pixabay images
- Basic analytics (views, uploads)
- Manual idea pushing
- Email approval flow
- SMTP auth

### Plan 2 — Creator · $79/month
- **100 Shorts/month**
- **5 YouTube Channels**
- All active formats (Horror + any Phase 2 formats as released)
- ElevenLabs OR Google TTS voices
- Priority video processing
- AI trend discovery (auto topic suggestions)
- Full analytics dashboard
- Channel health reports
- Custom scheduling (time slots per channel)
- Automated approval (no email click required)
- Blog access

### Plan 3 — Agency · $199/month
- **Unlimited Shorts**
- **Unlimited Channels**
- All formats including future
- All voice providers
- Fastest processing queue
- AI channel manager (auto decides content + format per channel)
- White-label ready (custom domain)
- API access (webhook triggers)
- Priority support
- Stripe billing management (self-serve)
- Advanced SEO tools for blog

**Billing Notes:**
- All plans: monthly subscription
- Stripe integration: planned (slot exists in DB, UI shows "coming soon" upgrade button for now)
- Free trial: 3 shorts, no credit card
- Overage: blocked + in-app notification to upgrade

---

## 9. Authentication System

### SMTP Email Auth Flow
1. User registers with email + password
2. FastAPI sends verification email via SMTP (configurable: Gmail, SendGrid, custom)
3. Email contains 6-digit OTP (valid 15 min) stored in Redis
4. User enters OTP → account activated
5. JWT access token (15 min) + refresh token (7 days) issued
6. Refresh token stored in httpOnly cookie
7. Password reset: same OTP flow via email

### .env SMTP Config
```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=noreply@viralflux.io
SMTP_PASSWORD=your_app_password
SMTP_FROM_NAME=ViralFlux
```

### YouTube OAuth
- Each channel requires OAuth 2.0 connection (Google Cloud Console credentials)
- Tokens stored encrypted in DB per channel record
- Auto-refresh on expiry
- User connects channel via "Connect Channel" button → Google OAuth popup → callback stored

---

## 10. Database Schema (PostgreSQL)

```sql
-- Users
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  full_name VARCHAR(255),
  is_verified BOOLEAN DEFAULT FALSE,
  is_active BOOLEAN DEFAULT TRUE,
  plan_id UUID REFERENCES plans(id),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Plans
CREATE TABLE plans (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(50) NOT NULL,  -- 'starter', 'creator', 'agency'
  price_usd DECIMAL(10,2) NOT NULL,
  shorts_per_month INTEGER,  -- NULL = unlimited
  channels_limit INTEGER,    -- NULL = unlimited
  features JSONB,
  stripe_price_id VARCHAR(255)  -- for future Stripe
);

-- YouTube Channels
CREATE TABLE youtube_channels (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  channel_name VARCHAR(255) NOT NULL,
  youtube_channel_id VARCHAR(100),
  oauth_access_token TEXT,   -- encrypted
  oauth_refresh_token TEXT,  -- encrypted
  oauth_expiry TIMESTAMPTZ,
  default_voice_provider VARCHAR(50) DEFAULT 'edge-tts',
  default_voice_id VARCHAR(100) DEFAULT 'en-US-GuyNeural',
  default_music_category VARCHAR(50) DEFAULT 'horror_ambient',
  default_format VARCHAR(50) DEFAULT 'horror_story',
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Content Formats (plugin registry)
CREATE TABLE content_formats (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  slug VARCHAR(50) UNIQUE NOT NULL,  -- 'horror_story', 'brainrot', etc.
  name VARCHAR(100) NOT NULL,
  description TEXT,
  is_active BOOLEAN DEFAULT FALSE,
  config_schema JSONB,  -- JSON schema for format-specific settings
  min_plan VARCHAR(50) DEFAULT 'starter'
);

-- Video Jobs
CREATE TABLE video_jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),
  channel_id UUID NOT NULL REFERENCES youtube_channels(id),
  format_slug VARCHAR(50) NOT NULL,
  status VARCHAR(50) DEFAULT 'queued',
  -- Status flow: queued → generating → pending_approval → approved → uploading → posted → failed
  topic TEXT,
  source_url TEXT,  -- Reddit URL or manual input
  script TEXT,
  seo_title VARCHAR(100),
  seo_description TEXT,
  seo_tags TEXT[],
  voice_provider VARCHAR(50),
  voice_id VARCHAR(100),
  video_path TEXT,
  youtube_video_id VARCHAR(50),
  youtube_url TEXT,
  cost_usd DECIMAL(10,4),
  error_message TEXT,
  approval_token VARCHAR(100),
  approved_at TIMESTAMPTZ,
  posted_at TIMESTAMPTZ,
  scheduled_for TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Schedule Config (per channel)
CREATE TABLE channel_schedules (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  channel_id UUID UNIQUE NOT NULL REFERENCES youtube_channels(id),
  is_enabled BOOLEAN DEFAULT FALSE,
  frequency_days INTEGER DEFAULT 2,  -- post every N days
  post_time TIME DEFAULT '18:00:00',
  timezone VARCHAR(50) DEFAULT 'America/Los_Angeles',
  require_approval BOOLEAN DEFAULT TRUE,
  approval_email VARCHAR(255),
  auto_topic BOOLEAN DEFAULT TRUE,  -- AI picks topic
  topics_queue TEXT[],  -- manual topic queue
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Assets (images, music tracks)
CREATE TABLE assets (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  type VARCHAR(30) NOT NULL,  -- 'music', 'background_video', 'image'
  category VARCHAR(50),  -- 'horror_ambient', 'gameplay_minecraft', etc.
  file_path TEXT NOT NULL,
  source_url TEXT,
  license VARCHAR(50) DEFAULT 'cc0',
  tags TEXT[],
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Blog Posts
CREATE TABLE blog_posts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  author_id UUID REFERENCES users(id),
  title VARCHAR(255) NOT NULL,
  slug VARCHAR(255) UNIQUE NOT NULL,
  content TEXT NOT NULL,  -- Markdown
  excerpt TEXT,
  meta_title VARCHAR(255),
  meta_description VARCHAR(300),
  og_image_url TEXT,
  featured_image_url TEXT,
  status VARCHAR(20) DEFAULT 'draft',  -- draft, published, archived
  tags TEXT[],
  reading_time_min INTEGER,
  published_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Analytics snapshots
CREATE TABLE video_analytics (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id UUID REFERENCES video_jobs(id),
  youtube_video_id VARCHAR(50),
  views INTEGER DEFAULT 0,
  likes INTEGER DEFAULT 0,
  comments INTEGER DEFAULT 0,
  watch_time_hours DECIMAL(10,2),
  snapshot_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 11. API Endpoints (FastAPI)

### Auth (`/api/v1/auth`)
```
POST /register          — email, password, full_name
POST /verify-otp        — email, otp
POST /login             — email, password → JWT
POST /refresh           — refresh token cookie → new JWT
POST /forgot-password   — email → send OTP
POST /reset-password    — email, otp, new_password
POST /logout            — clear cookie
GET  /me                — current user profile
```

### Channels (`/api/v1/channels`)
```
GET    /                — list user's channels
POST   /                — create channel (name, settings)
GET    /{id}            — channel detail
PUT    /{id}            — update settings
DELETE /{id}            — remove channel
POST   /{id}/connect-youtube — initiate OAuth flow
GET    /{id}/oauth-callback  — OAuth callback
POST   /{id}/schedule   — set schedule config
GET    /{id}/analytics  — channel analytics summary
```

### Videos (`/api/v1/videos`)
```
GET    /                — list jobs (paginated, filterable by status/channel)
POST   /generate        — trigger manual generation {channel_id, topic?, format?}
GET    /{id}            — job detail + status
GET    /{id}/preview    — serve preview MP4
POST   /{id}/approve    — approve for posting
POST   /{id}/reject     — reject (with optional note)
DELETE /{id}            — delete job
POST   /bulk-generate   — queue multiple videos
GET    /approve/{token} — email approval link handler (no auth required)
```

### Dashboard (`/api/v1/dashboard`)
```
GET  /stats             — totals: videos posted, views, cost this month
GET  /activity          — recent job activity feed
GET  /trending-topics   — AI-suggested topics (Gemini analysis)
GET  /channel-health    — per-channel performance summary
```

### Plans (`/api/v1/plans`)
```
GET  /              — list all plans
GET  /current       — user's current plan + usage
POST /upgrade       — initiate plan change (Stripe placeholder)
```

### Blog (`/api/v1/blog`) — Admin only for write, public for read
```
GET    /posts           — list published posts (public)
GET    /posts/{slug}    — single post by slug (public)
POST   /posts           — create post (admin)
PUT    /posts/{id}      — update post (admin)
DELETE /posts/{id}      — delete post (admin)
POST   /posts/{id}/publish — publish draft
GET    /sitemap         — XML sitemap for blog
```

### n8n Webhooks (`/api/v1/webhooks/n8n`) — Internal only
```
POST /job-complete      — n8n signals video generation done
POST /schedule-trigger  — n8n triggers scheduled generation
```

---

## 12. Frontend Pages & Routes

### Marketing (Public)
```
/                   — Landing page
/pricing            — Pricing plans + feature comparison table
/blog               — Blog index
/blog/[slug]        — Blog post
/about              — About page (simple)
```

### Auth
```
/login              — Login form
/register           — Register form
/verify             — OTP verification
/forgot-password    — Password reset request
/reset-password     — New password form
```

### Dashboard (Protected — requires auth)
```
/dashboard          — Overview: stats, recent activity, quick actions
/dashboard/channels         — Channel list + add new channel
/dashboard/channels/[id]    — Channel detail: settings, schedule, analytics
/dashboard/channels/[id]/connect — YouTube OAuth connect flow
/dashboard/videos           — All video jobs (filterable grid)
/dashboard/videos/new       — Manual video creation form
/dashboard/videos/[id]      — Job detail + preview player + approve/reject
/dashboard/analytics        — Charts: views, cost, performance over time
/dashboard/settings         — Account settings, plan, API keys, voice config
/dashboard/blog             — Blog post manager (admin only)
/dashboard/blog/new         — Create post (rich markdown editor)
/dashboard/blog/[id]/edit   — Edit post
```

### Landing Page Sections (in order)
1. **Hero** — Bold headline "Automate Your YouTube Shorts Empire", subtitle, CTA buttons (Start Free / See Demo), animated video preview mockup on right
2. **Social Proof** — "X shorts generated", "X channels managed", "X views driven"
3. **How It Works** — 4-step visual: Pick Topic → AI Writes → Video Built → Posted to YouTube
4. **Features Grid** — 6 cards: Multi-channel, AI story engine, Auto-posting, Trend detection, Cost tracking, Analytics
5. **Formats Showcase** — Horror Story card (active), + 4 "Coming Soon" format cards
6. **Pricing** — 3-column pricing table with feature comparison
7. **Blog Preview** — Latest 3 blog posts
8. **CTA Banner** — "Start automating today — your first 3 shorts are free"
9. **Footer** — Links, social, copyright

---

## 13. n8n Workflows

Store workflow JSON files in `/n8n/workflows/`. n8n reads from this folder on startup.

### Workflow 1: `video_generation_trigger.json`
- **Trigger:** Webhook (called by FastAPI when job queued)
- **Steps:** Validate job ID → Call FastAPI `/api/v1/videos/{id}` to get job data → Execute Python video pipeline via SSH/exec → Poll for completion → Call FastAPI webhook on complete
- **Error handling:** On failure → update job status to 'failed' → send error email

### Workflow 2: `scheduled_posting.json`
- **Trigger:** Cron (runs every 30 min)
- **Steps:** Call FastAPI `/api/v1/channels` to get channels with due schedules → For each due channel: call `/api/v1/videos/generate` → Log to Google Sheets (optional)

### Workflow 3: `trend_discovery.json`
- **Trigger:** Cron (daily at 6 AM)
- **Steps:** Fetch Reddit r/nosleep, r/creepypasta trending → Fetch Google Trends data → Pass to Gemini Flash for topic scoring → Store top 10 suggestions in Redis cache → Available via `/api/v1/dashboard/trending-topics`

### Workflow 4: `approval_reminder.json`
- **Trigger:** Cron (every 2 hours)
- **Steps:** Query DB for jobs in 'pending_approval' > 12 hours → Send reminder email with approve link

### Workflow 5: `analytics_sync.json`
- **Trigger:** Cron (daily at 2 AM)
- **Steps:** For each posted video → Call YouTube Analytics API → Store snapshot in `video_analytics` table

---

## 14. Folder Structure

```
viralflux/
├── docker-compose.yml              ← Single source of truth for all services
├── .env.example                    ← All env vars documented
├── .env                            ← NOT committed to git
├── Makefile                        ← dev shortcuts (make up, make logs, make migrate)
│
├── nginx/
│   ├── nginx.conf                  ← Main config with upstream proxy rules
│   └── conf.d/
│       └── viralflux.conf
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py                 ← FastAPI app init, CORS, router registration
│       ├── core/
│       │   ├── config.py           ← Pydantic Settings (reads .env)
│       │   ├── security.py         ← JWT, password hashing
│       │   ├── database.py         ← SQLAlchemy engine, session
│       │   └── dependencies.py     ← FastAPI deps (get_db, get_current_user)
│       ├── api/
│       │   └── v1/
│       │       ├── __init__.py
│       │       ├── auth.py
│       │       ├── channels.py
│       │       ├── videos.py
│       │       ├── dashboard.py
│       │       ├── plans.py
│       │       ├── blog.py
│       │       └── webhooks.py
│       ├── models/
│       │   ├── user.py
│       │   ├── channel.py
│       │   ├── video_job.py
│       │   ├── plan.py
│       │   ├── blog.py
│       │   └── analytics.py
│       ├── schemas/
│       │   ├── user.py
│       │   ├── channel.py
│       │   ├── video.py
│       │   └── blog.py
│       ├── services/
│       │   ├── llm/
│       │   │   ├── __init__.py
│       │   │   ├── base.py         ← LLMService abstract base
│       │   │   ├── gemini.py       ← Gemini Flash 2.5 Lite (creative)
│       │   │   └── openai_svc.py   ← GPT-4o-mini (analytical/SEO)
│       │   ├── tts/
│       │   │   ├── __init__.py
│       │   │   ├── base.py
│       │   │   ├── elevenlabs.py
│       │   │   ├── google_tts.py
│       │   │   └── edge_tts.py
│       │   ├── video/
│       │   │   ├── __init__.py
│       │   │   ├── pipeline.py     ← Orchestrates full video build
│       │   │   ├── ffmpeg_utils.py ← All FFmpeg commands
│       │   │   └── whisper_svc.py  ← Caption generation
│       │   ├── formats/
│       │   │   ├── __init__.py
│       │   │   ├── base.py         ← FormatPlugin abstract class
│       │   │   ├── horror_story.py ← Phase 1 active format
│       │   │   ├── brainrot.py     ← Phase 2 stub
│       │   │   └── ranking.py      ← Phase 2 stub
│       │   ├── assets/
│       │   │   ├── pexels.py
│       │   │   ├── pixabay.py
│       │   │   └── music_library.py
│       │   ├── youtube_service.py  ← OAuth + upload
│       │   └── email_service.py    ← SMTP
│       ├── workers/
│       │   ├── celery_app.py
│       │   └── tasks/
│       │       ├── video_tasks.py  ← generate_video Celery task
│       │       └── analytics_tasks.py
│       └── alembic/
│           ├── alembic.ini
│           └── versions/
│
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── tailwind.config.ts          ← Red theme tokens
│   ├── components.json             ← shadcn config
│   └── src/
│       ├── app/
│       │   ├── (marketing)/
│       │   │   ├── page.tsx        ← Landing page
│       │   │   ├── pricing/page.tsx
│       │   │   └── blog/
│       │   │       ├── page.tsx
│       │   │       └── [slug]/page.tsx
│       │   ├── (auth)/
│       │   │   ├── login/page.tsx
│       │   │   ├── register/page.tsx
│       │   │   └── verify/page.tsx
│       │   └── dashboard/
│       │       ├── layout.tsx      ← Sidebar + topbar
│       │       ├── page.tsx
│       │       ├── channels/
│       │       ├── videos/
│       │       ├── analytics/
│       │       ├── settings/
│       │       └── blog/
│       ├── components/
│       │   ├── ui/                 ← shadcn auto-generated
│       │   ├── landing/
│       │   │   ├── Hero.tsx
│       │   │   ├── HowItWorks.tsx
│       │   │   ├── Features.tsx
│       │   │   ├── Formats.tsx
│       │   │   ├── PricingSection.tsx
│       │   │   └── Footer.tsx
│       │   ├── dashboard/
│       │   │   ├── Sidebar.tsx
│       │   │   ├── Topbar.tsx
│       │   │   ├── VideoCard.tsx
│       │   │   ├── ChannelCard.tsx
│       │   │   ├── StatsCard.tsx
│       │   │   ├── VideoPlayer.tsx
│       │   │   ├── GenerateModal.tsx
│       │   │   └── ScheduleConfig.tsx
│       │   └── shared/
│       │       ├── ThemeToggle.tsx
│       │       └── LoadingSpinner.tsx
│       ├── lib/
│       │   ├── api.ts              ← Axios instance with JWT interceptor
│       │   ├── auth.ts             ← Auth helpers
│       │   └── utils.ts
│       └── store/
│           ├── authStore.ts        ← Zustand auth state
│           └── uiStore.ts
│
├── n8n/
│   └── workflows/
│       ├── video_generation_trigger.json
│       ├── scheduled_posting.json
│       ├── trend_discovery.json
│       ├── approval_reminder.json
│       └── analytics_sync.json
│
├── assets/
│   ├── music/
│   │   ├── horror_ambient/         ← Pre-curated .mp3 files
│   │   ├── upbeat_hype/
│   │   └── cinematic_epic/
│   └── gameplay/                   ← Future: background video clips
│
└── media/                          ← Runtime video output (mounted volume)
    ├── previews/
    └── final/
```

---

## 15. Docker Compose

```yaml
# docker-compose.yml
version: '3.9'

services:

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - ./media:/media:ro
    depends_on:
      - frontend
      - backend
      - n8n
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    env_file: .env
    environment:
      - NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
      - NEXT_PUBLIC_APP_URL=${NEXT_PUBLIC_APP_URL}
    depends_on:
      - backend
    restart: unless-stopped

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    env_file: .env
    volumes:
      - ./media:/app/media
      - ./assets:/app/assets:ro
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: celery -A app.workers.celery_app worker --loglevel=info --concurrency=2
    env_file: .env
    volumes:
      - ./media:/app/media
      - ./assets:/app/assets:ro
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  postgres:
    image: postgres:16-alpine
    env_file: .env
    environment:
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped

  n8n:
    image: n8nio/n8n:latest
    env_file: .env
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=${N8N_USER}
      - N8N_BASIC_AUTH_PASSWORD=${N8N_PASSWORD}
      - N8N_HOST=${N8N_HOST}
      - N8N_PORT=5678
      - N8N_PROTOCOL=http
      - WEBHOOK_URL=${N8N_WEBHOOK_URL}
      - DB_TYPE=postgresdb
      - DB_POSTGRESDB_HOST=postgres
      - DB_POSTGRESDB_PORT=5432
      - DB_POSTGRESDB_DATABASE=${N8N_DB_NAME}
      - DB_POSTGRESDB_USER=${POSTGRES_USER}
      - DB_POSTGRESDB_PASSWORD=${POSTGRES_PASSWORD}
      - N8N_ENCRYPTION_KEY=${N8N_ENCRYPTION_KEY}
      - GENERIC_TIMEZONE=${TIMEZONE}
    volumes:
      - n8n_data:/home/node/.n8n
      - ./n8n/workflows:/home/node/.n8n/workflows:ro
    depends_on:
      - postgres
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  n8n_data:
```

---

## 16. Centralized .env File

```bash
# ============================================================
# ViralFlux — Master Environment Configuration
# Copy this to .env and fill in all values
# NEVER commit .env to git
# ============================================================

# ── App ─────────────────────────────────────────────────────
APP_ENV=production
APP_SECRET_KEY=generate-a-long-random-string-here-min-64-chars
APP_URL=https://viralflux.io
NEXT_PUBLIC_APP_URL=https://viralflux.io
NEXT_PUBLIC_API_URL=https://viralflux.io/api/v1
TIMEZONE=America/Los_Angeles

# ── Database ─────────────────────────────────────────────────
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=viralflux
POSTGRES_USER=viralflux_user
POSTGRES_PASSWORD=strong_password_here
DATABASE_URL=postgresql://viralflux_user:strong_password_here@postgres:5432/viralflux

# ── Redis ───────────────────────────────────────────────────
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

# ── Auth / JWT ───────────────────────────────────────────────
JWT_SECRET_KEY=another-long-random-string-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# ── SMTP (Email) ─────────────────────────────────────────────
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=noreply@viralflux.io
SMTP_PASSWORD=your_gmail_app_password
SMTP_FROM_NAME=ViralFlux
SMTP_FROM_EMAIL=noreply@viralflux.io

# ── LLMs ────────────────────────────────────────────────────
# Primary — Gemini Flash (creative/script generation)
GOOGLE_AI_API_KEY=your_google_ai_studio_key
GEMINI_MODEL=gemini-2.5-flash-lite  # Update to latest Gemini Flash as of June 2026

# Secondary — GPT-4o-mini (SEO/analytics/decisions)
OPENAI_API_KEY=sk-your-openai-key
OPENAI_MODEL=gpt-4o-mini

# ── Voice Providers ──────────────────────────────────────────
ELEVENLABS_API_KEY=your_elevenlabs_key
GOOGLE_TTS_API_KEY=your_google_cloud_key
# edge-tts requires no API key

# ── Media Assets APIs ────────────────────────────────────────
PEXELS_API_KEY=your_pexels_key
PIXABAY_API_KEY=your_pixabay_key
UNSPLASH_ACCESS_KEY=your_unsplash_key

# ── YouTube / Google OAuth ───────────────────────────────────
YOUTUBE_CLIENT_ID=your_google_oauth_client_id
YOUTUBE_CLIENT_SECRET=your_google_oauth_client_secret
YOUTUBE_REDIRECT_URI=https://viralflux.io/api/v1/channels/oauth-callback

# ── Reddit (for trend/story discovery) ─────────────────────
REDDIT_CLIENT_ID=your_reddit_app_id
REDDIT_CLIENT_SECRET=your_reddit_secret
REDDIT_USER_AGENT=ViralFlux/1.0

# ── Stripe (future — keep slot ready) ───────────────────────
STRIPE_SECRET_KEY=sk_live_placeholder
STRIPE_PUBLISHABLE_KEY=pk_live_placeholder
STRIPE_WEBHOOK_SECRET=whsec_placeholder

# ── n8n ─────────────────────────────────────────────────────
N8N_USER=admin
N8N_PASSWORD=strong_n8n_password
N8N_HOST=viralflux.io
N8N_WEBHOOK_URL=https://viralflux.io/n8n/
N8N_DB_NAME=n8n
N8N_ENCRYPTION_KEY=generate-32-char-random-key

# ── Video Processing ─────────────────────────────────────────
FFMPEG_PATH=/usr/bin/ffmpeg
WHISPER_MODEL=base  # tiny/base/small/medium — base is best cost/quality
MAX_VIDEO_DURATION_SEC=60
VIDEO_RESOLUTION=1080x1920

# ── Storage ──────────────────────────────────────────────────
MEDIA_DIR=/app/media
ASSETS_DIR=/app/assets
MAX_STORAGE_GB=50
```

---

## 17. Nginx Configuration

```nginx
# nginx/conf.d/viralflux.conf

upstream frontend {
    server frontend:3000;
}
upstream backend {
    server backend:8000;
}
upstream n8n {
    server n8n:5678;
}

server {
    listen 80;
    server_name viralflux.io www.viralflux.io;
    
    # Redirect to HTTPS in production
    # return 301 https://$server_name$request_uri;

    client_max_body_size 500M;

    # API
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 600s;
    }

    # n8n
    location /n8n/ {
        proxy_pass http://n8n/;
        proxy_set_header Host $host;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Media files (video previews)
    location /media/ {
        alias /media/;
        expires 1h;
        add_header Cache-Control "public";
    }

    # Frontend (catch all)
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 18. Blog & SEO System

### Blog Features
- Markdown editor in dashboard (react-md-editor or similar)
- Auto-generate slug from title
- Meta title, meta description, OG image fields
- Tags + categories
- Reading time auto-calculated
- Draft → Publish workflow
- Scheduled publishing (publish_at field)

### SEO Implementation (Next.js)
```typescript
// Each blog post page generates proper metadata
export async function generateMetadata({ params }): Promise<Metadata> {
  const post = await getPost(params.slug)
  return {
    title: post.meta_title || post.title,
    description: post.meta_description || post.excerpt,
    openGraph: {
      title: post.title,
      description: post.excerpt,
      images: [post.og_image_url],
      type: 'article',
      publishedTime: post.published_at,
    },
    alternates: {
      canonical: `https://viralflux.io/blog/${post.slug}`
    }
  }
}
```

### Auto-generated SEO Pages
- `/sitemap.xml` — includes all blog posts + static pages
- `/robots.txt` — allows all crawlers, points to sitemap
- Blog post pages use Next.js static generation where possible
- Schema.org JSON-LD for article structured data

---

## 19. Manual Video Generation (Dashboard)

Users can push ideas manually from the dashboard:
- **Quick Generate** button → modal with fields:
  - Select channel
  - Format (Horror Story, etc.)
  - Topic input (optional — AI picks if blank)
  - Voice override (optional)
  - Schedule or post immediately
- AI fills any blank fields automatically
- Real-time job status updates via polling or WebSocket
- Preview appears in dashboard when ready
- One-click approve → posts to YouTube

---

## 20. AI Channel Manager Logic

When `auto_topic = true` for a channel:

1. **Trend Discovery** (Gemini Flash) — daily job fetches:
   - Reddit r/nosleep, r/creepypasta hot posts
   - Google Trends for horror/story keywords
   - Analyze channel's past performance (what did well)
   
2. **Topic Scoring** (GPT-4o-mini) — returns JSON:
   ```json
   {
     "recommended_topic": "The Cabin in the Woods — Reddit Story",
     "source_url": "https://reddit.com/...",
     "confidence_score": 0.87,
     "reasoning": "High engagement on r/nosleep, 2.1k upvotes, fits channel horror theme",
     "alternative_topics": ["...", "..."]
   }
   ```

3. **Channel Decision** — GPT-4o-mini advises:
   - Post on existing channel vs. suggest new channel
   - Best posting time based on past analytics
   - Format recommendation based on trend type

All suggestions shown in dashboard "AI Recommendations" panel. User can override or approve in one click.

---

## 21. Build Instructions for Claude Code

### Step 1: Environment Setup
1. Create repo structure from folder tree in Section 14
2. Create `docker-compose.yml` from Section 15
3. Create `.env.example` from Section 16 (all values commented/empty)
4. Create `Makefile` with: `up`, `down`, `logs`, `migrate`, `shell-backend`, `shell-frontend`

### Step 2: Database
1. Create all SQLAlchemy models from schema in Section 10
2. Set up Alembic migrations
3. Create seed script: insert 3 default plans, 5 content formats (1 active, 4 inactive)

### Step 3: Backend Core
1. FastAPI app with all routers from Section 11
2. JWT auth middleware
3. SMTP email service (OTP flow)
4. All Pydantic schemas

### Step 4: Services Layer
1. `LLMService` base class + Gemini + OpenAI implementations
2. `TTSService` base class + ElevenLabs + Google TTS + edge-tts
3. `FormatPlugin` base class + `HorrorStoryFormat` (fully implemented)
4. `VideoService` with FFmpeg pipeline for horror story format
5. `YouTubeService` for OAuth + upload
6. `AssetService` for Pexels/Pixabay image fetching

### Step 5: Celery Worker
1. Celery app with Redis broker
2. `generate_video` task that runs full pipeline
3. Error handling + status updates to DB

### Step 6: n8n Workflows
1. Import all 5 workflow JSON files to n8n on startup
2. Workflows should call FastAPI webhooks (use internal Docker network URLs)

### Step 7: Frontend
1. Next.js app with App Router
2. Tailwind red theme (primary: `#E5192A`)
3. shadcn/ui installed + configured
4. Dark mode via next-themes
5. All pages/routes from Section 12
6. Landing page with all sections from Section 12

### Step 8: Landing Page (Priority — Make It Premium)
The landing page must feel high-end SaaS, not a template. Requirements:
- Dark background `#0A0A0A` with red glow accents
- Animated gradient hero section
- Floating mockup/screenshot of dashboard
- Smooth scroll animations (framer-motion)
- Proper light mode toggle
- Mobile responsive
- Fast load — use Next.js Image optimization

### Step 9: Integration Testing
1. Test full pipeline: manual generate → video created → preview → approve → YouTube upload
2. Test schedule flow: schedule trigger → video queued → generated → posted
3. Test auth: register → OTP → login → JWT → protected routes

### Step 10: Docker Build
1. Verify all services start with `docker-compose up`
2. Nginx routes all traffic correctly
3. n8n workflows import on first boot
4. Alembic migrations run on backend startup
5. Default plans seeded on first boot

---

## 22. Cost Per Video (Target Validation)

| Item | Provider | Cost |
|---|---|---|
| Script generation (Gemini Flash) | Google AI | ~$0.001 |
| SEO generation (GPT-4o-mini) | OpenAI | ~$0.001 |
| Voice (edge-tts free) | Free | $0 |
| Voice (ElevenLabs, ~900 chars) | ElevenLabs | ~$0.003 |
| Images (Pexels API) | Free | $0 |
| Whisper (local) | Self-hosted | $0 |
| FFmpeg processing | Self-hosted | $0 |
| YouTube upload | Google API | $0 |
| **Total (free voice)** | | **~$0.002** |
| **Total (ElevenLabs voice)** | | **~$0.005** |

✅ **Massively under Sunny's $1 target.** Even at 100 videos/month with ElevenLabs: **$0.50 total LLM+TTS cost**.

---

## 23. Key Non-Negotiables (From Meeting)

1. **Cost first** — Never let a format exceed $0.50/video. If a new format would cost more, gate it behind Agency plan or add a cost warning.
2. **Story is the product** — Script quality from Gemini must be prioritized. The visual pipeline is commodity; the hook line at second 0 is everything.
3. **Channel identity** — Each channel must have a locked voice. Don't mix voices within a channel.
4. **Full automation is the dream** — Email approval is a safety net, not the workflow. Auto-approval option must exist.
5. **Modular formats** — New formats must be addable without touching core pipeline code. FormatPlugin pattern is mandatory.
6. **Under $1 is a product promise** — Show cost estimate on every video generation card in the dashboard.

---

*Plan Version: 1.0 — June 2026*
*Prepared by: Aisha Rahib for Sunny Singh (ViralFlux project)*
