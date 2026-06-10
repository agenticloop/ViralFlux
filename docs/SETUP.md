# ViralFlux — Setup Guide

This guide walks you from a bare server or developer machine to a fully running ViralFlux instance in under 20 minutes.

---

## 1. Prerequisites

| Requirement | Minimum Version | Notes |
|---|---|---|
| Docker | 24.0+ | `docker --version` |
| Docker Compose | v2 (built-in plugin) | `docker compose version` |
| git | Any recent | For cloning the repo |
| RAM | 4 GB minimum | 8 GB recommended for smooth local dev |
| Disk | 20 GB free | Media output can grow; 50 GB+ for production |
| OS | Linux, macOS, or WSL2 | Native Windows is not supported |

Install Docker by following the official guide at https://docs.docker.com/engine/install/.
Verify both tools are available before proceeding:

```bash
docker --version          # Docker version 24.x.x
docker compose version    # Docker Compose version v2.x.x
```

---

## 2. Clone the Repository

```bash
git clone https://github.com/your-org/viralflux.git
cd viralflux
```

---

## 3. Configure Environment Variables

ViralFlux uses a single centralized `.env` file. Copy the example file and fill in each section:

```bash
cp .env.example .env
```

Open `.env` in your editor. The file is organized into sections explained below.

### Section: App

```dotenv
APP_ENV=development          # Use "production" on a live server
APP_SECRET_KEY=...           # Min 64 random characters — used for session signing
APP_URL=http://localhost      # Public-facing URL (no trailing slash)
NEXT_PUBLIC_APP_URL=http://localhost
NEXT_PUBLIC_API_URL=http://localhost/api
TIMEZONE=America/New_York    # IANA timezone for scheduler and n8n
```

### Section: PostgreSQL

```dotenv
POSTGRES_HOST=postgres        # Service name inside Docker (do not change)
POSTGRES_PORT=5432
POSTGRES_DB=viralflux
POSTGRES_USER=viralflux_user
POSTGRES_PASSWORD=...         # Use a strong password in production
DATABASE_URL=postgresql+asyncpg://viralflux_user:PASSWORD@postgres:5432/viralflux
```

The `DATABASE_URL` must match the three credentials above. SQLAlchemy uses `+asyncpg` as the async driver.

### Section: Redis / Celery

```dotenv
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1
```

These point at the Redis container by service name. No changes needed for local development.

### Section: JWT Authentication

```dotenv
JWT_SECRET_KEY=...                         # Separate secret from APP_SECRET_KEY
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
```

Generate a strong value with: `python -c "import secrets; print(secrets.token_hex(64))"`

### Section: SMTP / Email

```dotenv
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=noreply@yourdomain.com
SMTP_PASSWORD=...            # Gmail: use an App Password, not your account password
SMTP_FROM_NAME=ViralFlux
SMTP_FROM_EMAIL=noreply@yourdomain.com
```

Email is used for OTP verification and approval notifications. In development, if SMTP is not configured, OTPs are printed to the backend container log — check `make logs` after registration.

### Section: Encryption

```dotenv
ENCRYPTION_KEY=...   # 64-char hex string — encrypts YouTube OAuth tokens at rest
```

Generate with: `python -c "import secrets; print(secrets.token_hex(32))"`

---

## 4. API Keys

### Required Keys (service will not function without these)

| Key | Variable | Where to get it |
|---|---|---|
| Google AI (Gemini) | `GOOGLE_AI_API_KEY` | https://aistudio.google.com/app/apikey |
| Pexels | `PEXELS_API_KEY` | https://www.pexels.com/api/ (free) |
| OpenAI | `OPENAI_API_KEY` | https://platform.openai.com/api-keys |
| YouTube OAuth client ID | `YOUTUBE_CLIENT_ID` | Google Cloud Console → APIs & Services → Credentials |
| YouTube OAuth client secret | `YOUTUBE_CLIENT_SECRET` | Same as above |

**Google AI (Gemini)** drives all script and story generation. Without it, no videos can be created.

**Pexels** provides the stock images used in video backgrounds. Without it, the image sourcing step fails.

**OpenAI (GPT-4o-mini)** handles all SEO metadata generation (title, description, tags). Without it, videos are generated without SEO data.

**YouTube OAuth credentials** are required to connect a YouTube channel and upload videos. Set `YOUTUBE_REDIRECT_URI` to match your deployment URL:
- Local dev: `http://localhost/api/v1/channels/{channel_id}/oauth-callback`
- Production: `https://yourdomain.com/api/v1/channels/{channel_id}/oauth-callback`

Add the redirect URI to your Google Cloud Console OAuth app's authorized redirect URIs.

### Optional Keys (degrade gracefully without these)

| Key | Variable | Effect if missing |
|---|---|---|
| ElevenLabs | `ELEVENLABS_API_KEY` | Falls back to free edge-tts voice |
| Google TTS | `GOOGLE_TTS_API_KEY` | Falls back to edge-tts |
| Pixabay | `PIXABAY_API_KEY` | Only Pexels is used for images |
| Unsplash | `UNSPLASH_ACCESS_KEY` | Only Pexels/Pixabay used |
| Reddit | `REDDIT_CLIENT_ID` / `REDDIT_CLIENT_SECRET` | AI topic discovery from Reddit disabled |
| Stripe | `STRIPE_SECRET_KEY` / etc. | Billing UI shows "coming soon"; no payments |
| n8n | `N8N_PASSWORD` | n8n admin panel uses default (change this!) |

---

## 5. Start All Services

```bash
make up
```

This runs `docker compose up -d` which builds all images on first run (allow 3–5 minutes) and starts all containers in the background.

On first boot, the backend container automatically:
1. Runs Alembic database migrations (`alembic upgrade head`)
2. Seeds the database with the three default plans (Starter, Creator, Agency) and the content format registry

---

## 6. Verify Services Are Healthy

Check container health status:

```bash
make ps
```

You should see output similar to:

```
NAME        IMAGE               STATUS
postgres    postgres:16-alpine  Up (healthy)
redis       redis:7-alpine      Up (healthy)
backend     viralflux-backend   Up
worker      viralflux-backend   Up
frontend    viralflux-frontend  Up
n8n         n8nio/n8n:latest    Up
nginx       nginx:1.25-alpine   Up
```

Wait until `postgres` and `redis` show `(healthy)`. The `backend` container waits for both before starting, so if you see it restarting, just wait another 30 seconds.

To watch live logs from all services:

```bash
make logs
```

---

## 7. Access the Application

Once all services are running:

| Service | URL | Notes |
|---|---|---|
| Frontend (Next.js) | http://localhost | Main application |
| API documentation | http://localhost/api/docs | FastAPI Swagger UI (interactive) |
| API alternative docs | http://localhost/api/redoc | ReDoc-style reference |
| n8n workflow engine | http://localhost/n8n | Credentials: N8N_USER / N8N_PASSWORD from .env |

---

## 8. Register Your First Account

1. Go to http://localhost/register
2. Enter your email address, a password (minimum 8 characters), and your name
3. If SMTP is configured, check your email for a 6-digit OTP code
4. If SMTP is not configured (local dev), run `make logs` and find the line: `OTP for you@example.com: 123456`
5. Enter the OTP at http://localhost/verify
6. You are now logged in and on the dashboard

Your account is automatically assigned the **Starter** plan.

---

## 9. Connect a YouTube Channel

1. From the dashboard, click **Channels** in the sidebar
2. Click **Add Channel** and give it a name (e.g., "Horror Stories Channel")
3. Choose default voice, music category, and content format
4. Click **Save** to create the channel record
5. Click **Connect YouTube** on the new channel card
6. You will be redirected to Google's OAuth consent screen
7. Grant permission for ViralFlux to upload to your YouTube channel
8. You are redirected back and the channel shows as connected

You are now ready to generate your first video. Click **Generate Video**, select your channel, optionally enter a topic, and click **Generate**. The job is queued immediately and you can watch its status update in real time from the Videos page.

---

## Common Issues

**Backend container keeps restarting**
Check `make logs` for errors. The most common cause is a malformed `DATABASE_URL` in `.env`. Verify the username and password match `POSTGRES_USER` and `POSTGRES_PASSWORD`.

**OTP never arrives**
If `SMTP_USER` is not set, the OTP is logged to the backend container stdout. Run `make logs | grep OTP` to find it.

**YouTube OAuth redirect mismatch**
The `YOUTUBE_REDIRECT_URI` in `.env` must exactly match one of the authorized redirect URIs registered in your Google Cloud Console OAuth 2.0 client.

**n8n shows 401 Unauthorized**
The `N8N_USER` and `N8N_PASSWORD` from `.env` are used for basic auth. Include them in the URL or enter them in the browser prompt at http://localhost/n8n.
