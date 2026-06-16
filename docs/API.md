# ViralFlux — API Reference

---

## Base URL

All API endpoints are served under the `/api/v1/` prefix:

```
http://localhost/api/v1          (local development)
https://yourdomain.com/api/v1   (production)
```

Interactive documentation (Swagger UI) is available at `/api/docs`.
ReDoc-style documentation is available at `/api/redoc`.

---

## Authentication

ViralFlux uses JWT Bearer tokens for authentication.

### Access Token

Include the access token in the `Authorization` header for all protected endpoints:

```
Authorization: Bearer <access_token>
```

Access tokens expire after **15 minutes**. When a request returns `401 Unauthorized`, use the refresh endpoint to obtain a new access token.

### Refresh Token

The refresh token is stored in an `httpOnly` cookie named `refresh_token` scoped to the path `/api/v1/auth/refresh`. The browser sends it automatically when calling the refresh endpoint. Refresh tokens expire after **7 days**.

### Verification Requirement

Most dashboard endpoints require both a valid JWT token and a verified email address (`is_verified=True`). Endpoints that require verification are marked with `[Verified]` below.

---

## Error Response Format

All errors return JSON with a single `detail` field:

```json
{
  "detail": "Human-readable error message"
}
```

Common HTTP status codes:

| Code | Meaning |
|---|---|
| 400 | Bad request — validation failure or invalid state transition |
| 401 | Unauthorized — missing, expired, or invalid token |
| 402 | Payment Required — plan limit reached (upgrade required) |
| 403 | Forbidden — account deactivated |
| 404 | Not Found — resource does not exist or belongs to another user |
| 409 | Conflict — e.g., email already registered |
| 422 | Unprocessable Entity — Pydantic validation error (field-level detail) |
| 500 | Internal Server Error |

---

## Auth Endpoints

### POST /api/v1/auth/register

Register a new account. Sends a 6-digit OTP to the provided email address. The OTP expires after 15 minutes.

**Request body:**

```json
{
  "email": "user@example.com",
  "password": "minimum8chars",
  "full_name": "Sunny Singh"
}
```

`full_name` is optional. `password` must be at least 8 characters.

**Response (201 Created):**

```json
{
  "message": "Registration successful. Check your email for the OTP."
}
```

**Errors:** `409 Conflict` — email already registered.

---

### POST /api/v1/auth/verify-otp

Verify the 6-digit OTP received by email. On success, the account is activated and tokens are returned.

**Request body:**

```json
{
  "email": "user@example.com",
  "otp": "483921"
}
```

**Response (200 OK):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "full_name": "Sunny Singh",
    "is_verified": true,
    "is_active": true,
    "plan_id": "...",
    "created_at": "2026-06-09T12:00:00Z"
  }
}
```

The `refresh_token` cookie is set automatically. **Errors:** `400 Bad Request` — invalid or expired OTP.

---

### POST /api/v1/auth/login

Authenticate with email and password. Returns tokens.

**Request body:**

```json
{
  "email": "user@example.com",
  "password": "minimum8chars"
}
```

**Response (200 OK):** Same structure as `/verify-otp` above.

**Errors:** `401 Unauthorized` — invalid credentials. `403 Forbidden` — account deactivated.

---

### POST /api/v1/auth/refresh

Exchange the `refresh_token` cookie for a new access token. The browser sends the cookie automatically.

**Request:** No body. Requires the `refresh_token` httpOnly cookie.

**Response (200 OK):** Same structure as `/login`.

**Errors:** `401 Unauthorized` — refresh token missing, invalid, or expired.

---

### POST /api/v1/auth/forgot-password

Request a password reset OTP. Always returns success to prevent email enumeration — the OTP is only sent if the email exists.

**Request body:**

```json
{
  "email": "user@example.com"
}
```

**Response (200 OK):**

```json
{
  "message": "If that email exists, a reset code has been sent."
}
```

---

### POST /api/v1/auth/reset-password

Reset password using the OTP received by email.

**Request body:**

```json
{
  "email": "user@example.com",
  "otp": "219483",
  "new_password": "newpassword123"
}
```

**Response (200 OK):**

```json
{
  "message": "Password updated successfully."
}
```

---

### POST /api/v1/auth/logout

Clears the `refresh_token` cookie.

**Response (200 OK):**

```json
{
  "message": "Logged out."
}
```

---

### GET /api/v1/auth/me `[Verified]`

Returns the currently authenticated user's profile.

**Response (200 OK):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "full_name": "Sunny Singh",
  "is_verified": true,
  "is_active": true,
  "plan_id": "a1b2c3d4-...",
  "created_at": "2026-06-09T12:00:00Z"
}
```

---

## Channel Endpoints

All channel endpoints require `[Verified]` authentication.

### GET /api/v1/channels/

List all active YouTube channels belonging to the current user, including their schedule configuration.

**Response (200 OK):**

```json
[
  {
    "id": "channel-uuid",
    "user_id": "user-uuid",
    "channel_name": "Horror Stories Channel",
    "youtube_channel_id": "UCxxxxxxxxxxxxxxx",
    "oauth_expiry": "2026-07-09T12:00:00Z",
    "genre": "horror",
    "default_voice_id": "EXAVITQu4vr4xnSDxMaL",
    "default_music_category": "horror_ambient",
    "default_model_tier": "Balanced",
    "is_active": true,
    "created_at": "2026-06-09T12:00:00Z",
    "schedule": null
  }
]
```

`genre` is one of `horror`, `brainrot`, or `custom` (Pro/Agency). `default_voice_id` is an ElevenLabs voice ID. `default_model_tier` is `Lite` / `Balanced` / `Max` (availability gated by plan — see `pricing.md`).

---

### POST /api/v1/channels/

Create a new channel. Enforces the plan's `channels_limit`.

**Request body:**

```json
{
  "channel_name": "Horror Stories Channel",
  "genre": "horror",
  "default_voice_id": "EXAVITQu4vr4xnSDxMaL",
  "default_music_category": "horror_ambient",
  "default_model_tier": "Balanced"
}
```

`genre` must be allowed by the user's plan (Free: `horror` **or** `brainrot`; `custom` requires Pro+).

**Response (201 Created):** The created channel object (same structure as list item above).

**Errors:** `402 Payment Required` — channel limit for current plan reached.

---

### GET /api/v1/channels/{channel_id}

Get a single channel with its schedule configuration.

**Response (200 OK):** Single channel object.

---

### PUT /api/v1/channels/{channel_id}

Update channel settings. All fields are optional.

**Request body:**

```json
{
  "channel_name": "Creepy Tales",
  "genre": "horror",
  "default_voice_id": "pNInz6obpgDQGcFmaJgB",
  "default_music_category": "horror_ambient",
  "default_model_tier": "Max"
}
```

---

### DELETE /api/v1/channels/{channel_id}

Soft-delete a channel (`is_active = False`). Returns `204 No Content`.

---

### POST /api/v1/channels/{channel_id}/connect-youtube

Initiate the **direct** YouTube OAuth 2.0 flow (multi-account; PostProxy removed). Returns a Google OAuth authorization URL.

**Response (200 OK):**

```json
{
  "oauth_url": "https://accounts.google.com/o/oauth2/auth?client_id=...&scope=..."
}
```

Redirect the user to `oauth_url`. After they grant permission, Google redirects to the `YOUTUBE_REDIRECT_URI` which calls the callback endpoint below.

---

### GET /api/v1/channels/youtube/callback

OAuth callback handler (must match `YOUTUBE_REDIRECT_URI`). Exchanges the authorization code for tokens, stores them encrypted per channel, and fetches the YouTube channel ID. This endpoint is called automatically by Google's redirect — do not call it manually.

**Response (200 OK):**

```json
{
  "message": "YouTube channel connected successfully.",
  "channel_id": "channel-uuid"
}
```

---

### POST /api/v1/channels/{channel_id}/schedule

Create or update the posting schedule for a channel (upsert).

**Request body:**

```json
{
  "is_enabled": true,
  "frequency_days": 2,
  "post_time": "18:00:00",
  "timezone": "America/New_York",
  "require_approval": true,
  "approval_email": "sunny@example.com",
  "auto_topic": true,
  "topics_queue": ["The Cursed Lake", "Night at the Abandoned Mill"]
}
```

- `frequency_days`: post every N days
- `require_approval`: if false, videos are auto-approved and uploaded without email review
- `auto_topic`: if true, Gemini suggests a topic when the queue is empty (no Reddit/trend source)
- `topics_queue`: manual topic list; used in order before Gemini suggests if `auto_topic` is true

The `beat` scheduler's `scan_schedules` task reads these fields every 5 minutes to enqueue due posts.

---

### GET /api/v1/channels/{channel_id}/analytics

Returns aggregate analytics for a channel.

**Response (200 OK):**

```json
{
  "channel_id": "channel-uuid",
  "total_jobs": 45,
  "total_posted": 38,
  "total_views": 184200,
  "total_likes": 9100,
  "avg_views_per_video": 4847.4
}
```

---

## Video Endpoints

All video endpoints require `[Verified]` authentication unless noted.

### GET /api/v1/videos/

List video jobs for the current user. Supports pagination and filtering.

**Query parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `page` | integer | 1 | Page number (1-based) |
| `page_size` | integer | 20 | Items per page (max 100) |
| `status` | string | — | Filter by status (e.g., `pending_approval`, `posted`) |
| `channel_id` | UUID | — | Filter by channel |

**Response (200 OK):**

```json
{
  "items": [ /* VideoJobOut objects */ ],
  "total": 45,
  "page": 1,
  "page_size": 20
}
```

**Video status values:** `queued` → `generating` → `pending_approval` → `approved` → `uploading` → `posted`. Terminal states: `failed`, `rejected`.

---

### POST /api/v1/videos/generate

Queue a single video generation job. Returns `202 Accepted` immediately — the job runs asynchronously.

**Request body:**

```json
{
  "channel_id": "channel-uuid",
  "topic": "The night I heard something in the walls",
  "model_tier": "Balanced",
  "duration": "60s",
  "voice_id": "pNInz6obpgDQGcFmaJgB",
  "schedule_for": "2026-06-15T18:00:00Z"
}
```

All fields except `channel_id` are optional. The genre is taken from the channel. If `topic` is omitted, Gemini suggests one (no Reddit). If `model_tier`/`duration`/`voice_id` are omitted, the channel defaults are used. Tier and duration must be allowed by the user's plan (and the Max tier is subject to the monthly Max Quota — see `pricing.md`).

**Response (202 Accepted):**

```json
{
  "id": "job-uuid",
  "status": "queued",
  "channel_id": "channel-uuid",
  "genre": "horror",
  "model_tier": "Balanced",
  "duration": "60s",
  "topic": "The night I heard something in the walls",
  "script": null,
  "seo_title": null,
  "video_path": null,
  "youtube_url": null,
  "credits_charged": 34,
  "created_at": "2026-06-09T14:00:00Z",
  "updated_at": "2026-06-09T14:00:00Z",
  ...
}
```

Poll `GET /videos/{id}` to track job status. `credits_charged` is debited up front from the user's balance.

**Errors:** `402 Payment Required` — insufficient credits, or duration/tier/genre not allowed by the plan.

---

### GET /api/v1/videos/{job_id}

Get details and current status of a single video job.

**Response (200 OK):** Full `VideoJobOut` object (same structure as generate response, with fields populated as they become available during generation).

---

### GET /api/v1/videos/{job_id}/preview

Stream the generated MP4 file for in-browser preview.

**Response (200 OK):** `video/mp4` file stream.

**Errors:** `404 Not Found` — video not yet generated or file missing from disk.

---

### POST /api/v1/videos/{job_id}/approve

Approve a video for upload to YouTube. Only valid when `status=pending_approval`.

**Request body:**

```json
{
  "note": "Looks great!"
}
```

`note` is optional. The upload task is queued immediately after approval.

**Response (200 OK):** Updated `VideoJobOut` with `status=approved`.

---

### POST /api/v1/videos/{job_id}/reject

Reject a video. Valid when `status=pending_approval` or `status=approved`.

**Request body:**

```json
{
  "note": "Script needs rewrite"
}
```

**Response (200 OK):** Updated `VideoJobOut` with `status=rejected`.

---

### DELETE /api/v1/videos/{job_id}

Delete a video job and its associated file from disk.

**Response (204 No Content)**

---

### POST /api/v1/videos/bulk-generate

Queue up to 10 video jobs at once.

**Request body:**

```json
{
  "channel_id": "channel-uuid",
  "count": 3,
  "model_tier": "Lite",
  "duration": "30s",
  "topic_list": ["Story 1", "Story 2", "Story 3"]
}
```

`topic_list` is optional. If provided, topics are assigned in order; remaining jobs use a Gemini topic suggestion. The genre is taken from the channel. Credits for all jobs are debited up front; if the balance is insufficient the whole batch is rejected with `402`.

**Response (202 Accepted):** Array of `VideoJobOut` objects.

---

### GET /api/v1/videos/approve/{token}

Email approval link handler. **No authentication required.** Validates the `approval_token` from the approval email and approves the video.

**Path parameter:** `token` — the approval token from the email link.

**Response (200 OK):** Approved `VideoJobOut`.

---

## Dashboard Endpoints

All dashboard endpoints require `[Verified]` authentication.

### GET /api/v1/dashboard/stats

Summary statistics for the current user's account.

**Response (200 OK):**

```json
{
  "posted_this_month": 12,
  "total_posted": 84,
  "total_views": 420000,
  "credits_remaining": 2210,
  "credits_used_this_month": 390,
  "active_channels": 3
}
```

---

### GET /api/v1/dashboard/activity

Most recent 20 video jobs, ordered by creation time descending.

**Response (200 OK):**

```json
[
  {
    "id": "job-uuid",
    "status": "posted",
    "topic": "The Cabin in the Woods",
    "title": "She Found Something in the Cabin | Horror Short",
    "channel_id": "channel-uuid",
    "genre": "horror",
    "created_at": "2026-06-09T10:00:00Z",
    "posted_at": "2026-06-09T11:30:00Z",
    "credits_charged": 34
  }
]
```

---

### GET /api/v1/dashboard/topic-suggestions

Returns Gemini-suggested topics for a genre, generated on demand (no Reddit/trend cache — the old `trending-topics` endpoint and its n8n trend-discovery workflow were removed in v2).

**Query parameters:** `genre` (`horror` | `brainrot` | `custom`), `count` (default 5).

**Response (200 OK):**

```json
{
  "genre": "horror",
  "topics": [
    "The Watcher in the Woods",
    "Something Wrong at the Old Mill",
    "I Found My Grandfather's Diary",
    "The Night Shift at Pier 17",
    "She Texted Me from the Grave"
  ]
}
```

---

### GET /api/v1/dashboard/channel-health

Per-channel health summary: last post time, total videos, average view count.

**Response (200 OK):**

```json
{
  "channels": [
    {
      "channel_id": "channel-uuid",
      "channel_name": "Horror Stories Channel",
      "youtube_channel_id": "UCxxxxxxxxxxxxxxx",
      "last_posted_at": "2026-06-08T18:00:00Z",
      "total_videos": 38,
      "avg_views": 4847.4
    }
  ]
}
```

---

## Plan Endpoints

### GET /api/v1/plans/

List all available subscription plans (public — no authentication required).

**Response (200 OK):**

```json
[
  {
    "id": "plan-uuid",
    "name": "starter",
    "price_usd": "19.00",
    "monthly_credits": 850,
    "channels_limit": 2,
    "max_duration": "60s",
    "max_quota": 0,
    "features": {
      "genres": ["horror", "brainrot"],
      "model_tiers": ["Lite", "Balanced"],
      "analytics": "basic",
      "auto_approval": false,
      "community_voices": false
    },
    "stripe_price_id": null
  }
]
```

Plans (authoritative breakdown in `pricing.md`):
- `free` — $0, 30 credits, 1 channel, Lite only, Horror **or** Brainrot
- `starter` — $19/mo, 850 credits, 2 channels, Lite + Balanced
- `pro` — $49/mo, 2,600 credits, 5 channels, all tiers (30 Max/mo), custom genre
- `agency` — $129/mo, 8,000 credits, 15 channels, all tiers (120 Max/mo)

Users buy more credits via top-up packs (Spark/Boost/Surge/Blitz) on every plan. Stripe billing is **deferred** — `stripe_price_id` is currently `null`.

---

## Blog Endpoints

Read endpoints are public. Write endpoints require admin access.

### GET /api/v1/blog/posts

List published blog posts.

**Query parameters:** `page`, `page_size`, `tag` (filter by tag).

**Response (200 OK):** Paginated list of blog post summaries (without full content).

---

### GET /api/v1/blog/posts/{slug}

Get a single published blog post by slug.

**Response (200 OK):**

```json
{
  "id": "post-uuid",
  "title": "How We Generate Horror YouTube Shorts for Under $0.01",
  "slug": "how-we-generate-horror-youtube-shorts",
  "content": "## Introduction\n...",
  "excerpt": "A deep dive into our AI pipeline...",
  "meta_title": "...",
  "meta_description": "...",
  "tags": ["ai", "youtube", "automation"],
  "reading_time_min": 4,
  "published_at": "2026-06-09T09:00:00Z",
  "status": "published"
}
```

---

### POST /api/v1/blog/posts `[Admin]`

Create a blog post. Requires admin account (email listed in `ADMIN_EMAILS` env var).

### PUT /api/v1/blog/posts/{id} `[Admin]`

Update a blog post.

### DELETE /api/v1/blog/posts/{id} `[Admin]`

Delete a blog post.

### POST /api/v1/blog/posts/{id}/publish `[Admin]`

Transition a draft post to `published` status.

### GET /api/v1/blog/sitemap

Returns an XML sitemap of all published blog posts.

---

## Webhook Endpoints

Webhook endpoints are called by n8n workflows using the internal Docker network. They require a shared secret header to prevent unauthorized calls.

### Secret Header Requirement

All webhook endpoints require the header:

```
X-Webhook-Secret: <value-of-APP_SECRET_KEY>
```

If the header is missing or incorrect, the endpoint returns `401 Unauthorized`.

### POST /api/v1/webhooks/n8n/job-complete

Called by n8n when it detects a video generation step has completed outside the normal Celery flow.

**Request body:**

```json
{
  "job_id": "job-uuid",
  "status": "pending_approval",
  "video_path": "/app/media/previews/job-uuid.mp4"
}
```

---

### POST /api/v1/webhooks/n8n/schedule-trigger

Called by n8n's stateless cron workflows to ask the backend to run an action. n8n holds **no** tenant state — it only sends an `action`; the backend owns the per-tenant logic. This is a supplementary nudge on top of the primary `beat` scheduler.

**Request body:**

```json
{
  "action": "scan_schedules"
}
```

`action` is one of:

| Action | Effect (mirrors a beat task) |
|---|---|
| `scan_schedules` | Scan enabled channel schedules and enqueue any due posts |
| `sync_analytics` | Enqueue a YouTube Analytics refresh for all channels |
| `send_approval_reminders` | Email reminders for videos still awaiting approval |

**Response (200 OK):** `{ "success": true, "message": "...", "task_id": "..." }`
