# ViralFlux — Deployment Notes (shared EC2 alongside SkyPulse)

ViralFlux runs on the same EC2 host as SkyPulse, behind the shared host nginx.
See `/home/ec2-user/SERVER.md` for the host-wide multi-app convention.

The upstream repo assumes a dedicated Ubuntu server with its own nginx + certbot
on ports 80/443. That model would collide with SkyPulse. Instead of editing the
app, the host-specific adjustments are isolated in **`docker-compose.override.yml`**
(auto-merged by Docker Compose) plus two small edits to `docker-compose.yml`.

## What differs from the upstream repo

**`docker-compose.override.yml`** (new — all coexistence config lives here):
- All containers renamed `viralflux-*` (no clash with `skypulse-*`).
- Published ports bound to **127.0.0.1 only**, on unique numbers:
  frontend `3100`, backend `8100`, n8n `5778`. Postgres/Redis not published.
- `deploy.resources.limits` on every service. The Celery **worker is capped at 1
  CPU + concurrency 1** so video rendering can never eat both vCPUs and starve
  SkyPulse.
- Worker command fixed to consume the queues the app routes to:
  `-Q video,analytics,celery` (upstream omitted `-Q`, so those queues were never
  drained).
- n8n gets `N8N_PATH=/n8n/` so it serves correctly under the subdomain path.
- The repo's bundled **nginx service is disabled** via a compose profile — the host
  nginx is the front door.

**`docker-compose.yml`** (two edits):
- Backend & worker media bind changed `./media` → `/srv/viralflux/media` so the host
  nginx (running as user `nginx`, which cannot traverse `0700` `$HOME`) can serve
  `/media/` directly from disk.

**`scripts/init-n8n-db.sh`** (new): creates the dedicated `n8n` database inside
ViralFlux's Postgres on first init (the app DB is `viralflux`; n8n needs its own).

**`.env`**: generated with strong random secrets (APP/JWT/Fernet/Postgres/n8n).
Third-party API keys are placeholders (`REPLACE_ME_*`) — fill them to enable the
matching feature. URLs point at `https://viralflux.skypulseforge.com`.
`MAX_STORAGE_GB=8` (small disk). `ADMIN_EMAILS` grants admin to that signup.

## Operating

```bash
cd /home/ec2-user/viralflux
docker compose up -d            # starts all services (bundled nginx stays disabled)
docker compose ps
docker compose logs -f backend  # or worker / frontend / n8n
docker compose down             # stops ONLY ViralFlux (separate project from SkyPulse)
```

Host nginx vhost: `/etc/nginx/conf.d/viralflux.conf`
(`sudo nginx -t && sudo systemctl reload nginx` after edits).

## Filling in API keys later
Edit `.env`, replace the relevant `REPLACE_ME_*`, then:
```bash
docker compose up -d            # recreates containers that consume changed env
# (frontend NEXT_PUBLIC_* are build-time — rebuild if you change those:
#  docker compose up -d --build frontend)
```
