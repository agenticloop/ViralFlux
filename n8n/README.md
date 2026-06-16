# n8n — Supplementary Automation (NOT the primary scheduler)

n8n is a **thin, supplementary automator** for ViralFlux. It is **not** the
scheduler and it **holds no tenant state**.

## The golden rule

> **The primary scheduler is the backend Celery `beat` service.**

The DB-driven beat tasks live in `backend/app/workers/celery_app.py`:

| Task              | Cadence      | Responsibility                                   |
| ----------------- | ------------ | ------------------------------------------------ |
| `scan_schedules`  | every 5 min  | finds due channel schedules, enqueues generation |
| `sync_analytics`  | daily        | pulls YouTube analytics for all channels         |

Beat is a required service in `docker-compose.yml`. If beat is down, posting
automation stops — n8n cannot and must not cover for it.

## What n8n is allowed to do

Every workflow here is **stateless** and **multi-tenant-safe** by construction:

- It **only** calls backend endpoints, primarily the n8n webhook surface
  `POST /api/v1/webhooks/n8n/...` (authenticated with the `X-Webhook-Secret`
  header = `APP_SECRET_KEY`).
- It makes **no per-tenant decisions**: no "is this channel due", no staleness
  thresholds, no credit math, no model/voice selection. The backend owns all of
  that. n8n just asks the backend to "run X now".
- It stores **no tenant data** in n8n. Workflows carry only an `action` string
  and, at most, an opaque `job_id` echoed back from the backend.

This keeps tenant isolation entirely inside the backend (where auth, RLS-style
scoping, and credit accounting live) and lets n8n be swapped or disabled without
risking cross-tenant leakage.

## The workflows

| Workflow                        | Trigger             | What it does                                                                 |
| ------------------------------- | ------------------- | --------------------------------------------------------------------------- |
| `scheduled_posting.json`        | cron, every 30 min  | **Supplementary nudge.** Asks backend to run `scan_schedules`. Beat is primary. |
| `approval_reminder.json`        | cron, every 2 h     | **Supplementary nudge.** Asks backend to send reminders for pending approvals. |
| `analytics_sync.json`           | cron, daily 02:00   | **Supplementary nudge.** Asks backend to run `sync_analytics`. Beat is primary. |
| `video_generation_trigger.json` | inbound webhook     | Receives a `job_id`, validates it, delegates the run to the backend, echoes status. |

> `trend_discovery.json` was **removed** in v2 — Reddit/trend scraping is gone.
> No workflow here contains Reddit, PRAW, or any trending logic. If you add one,
> it must follow the golden rule above.

## Why both beat AND n8n?

Beat is authoritative. The cron workflows above are an idempotent safety net: if
beat ever misses a tick, the next n8n nudge asks the backend to scan again, and
the backend deduplicates. Because n8n only triggers backend-owned logic, running
both is safe and never double-posts.

## Operating

- Workflows are imported into n8n from these JSON files; they ship **inactive**
  (`"active": false`). Enable them in the n8n UI once `APP_SECRET_KEY` matches.
- n8n is reachable at `/n8n/` through nginx (basic-auth, see `.env`).
- Logs: `make logs` then filter the `n8n` service, or `docker compose logs n8n`.
