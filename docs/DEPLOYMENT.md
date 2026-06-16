# ViralFlux — Production Deployment Guide

This guide covers deploying ViralFlux on a fresh Ubuntu 22.04 LTS server with HTTPS, a firewall, and a backup strategy.

---

## 1. Server Requirements

| Resource | Minimum | Recommended |
|---|---|---|
| OS | Ubuntu 22.04 LTS | Ubuntu 22.04 LTS |
| CPU | 2 vCPU | 4 vCPU |
| RAM | 4 GB | 8 GB |
| Disk | 50 GB SSD | 100 GB SSD |
| Network | 100 Mbps | 1 Gbps |

**Why 50 GB minimum:** Each generated video is approximately 50–150 MB. 50 GB gives you headroom for ~300–1000 videos before the disk-cleanup cron triggers. The `MAX_STORAGE_GB` env var controls the threshold.

**DigitalOcean Droplet equivalent:** General Purpose 2 vCPU / 4 GB RAM / 80 GB NVMe ($36/month as of 2026) is a solid starting point.

---

## 2. Initial Server Setup

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install prerequisites
sudo apt-get install -y git curl ufw ca-certificates gnupg

# Install Docker (official method)
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Allow current user to run Docker without sudo
sudo usermod -aG docker $USER
newgrp docker

# Verify
docker --version
docker compose version
```

---

## 3. Clone and Configure

```bash
cd /opt
sudo git clone https://github.com/your-org/viralflux.git
sudo chown -R $USER:$USER /opt/viralflux
cd /opt/viralflux

# Create production .env
cp .env.example .env
nano .env
```

---

## 4. Production Environment Variables

The following variables require production-specific values. All others can be copied from `.env.example` with the placeholder values replaced.

```dotenv
# --- Required production changes ---

APP_ENV=production
APP_SECRET_KEY=<generate: python -c "import secrets; print(secrets.token_hex(64))">
APP_URL=https://yourdomain.com
FRONTEND_URL=https://yourdomain.com
NEXT_PUBLIC_APP_URL=https://yourdomain.com
NEXT_PUBLIC_API_URL=https://yourdomain.com/api/v1

POSTGRES_PASSWORD=<strong random password>
DATABASE_URL=postgresql+asyncpg://viralflux_user:<password>@postgres:5432/viralflux

JWT_SECRET_KEY=<generate: python -c "import secrets; print(secrets.token_hex(64))">

ENCRYPTION_KEY=<generate: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())">

# Email (Resend — SMTP removed)
RESEND_API_KEY=<from resend.com>
EMAIL_FROM=ViralFlux <noreply@yourdomain.com>

# LLM (Gemini-only, 3 tiers) + TTS (ElevenLabs-only) + Images (Imagen 4 Fast)
GOOGLE_AI_API_KEY=<from aistudio.google.com>
GEMINI_MODEL_LITE=gemini-3.1-flash-lite
GEMINI_MODEL_BALANCED=gemini-3.1-flash
GEMINI_MODEL_MAX=gemini-3.5-flash
ELEVENLABS_API_KEY=<from elevenlabs.io>
ELEVENLABS_MODEL=eleven_flash_v2_5
ELEVENLABS_BASE_URL=https://api.elevenlabs.io
IMAGE_PROVIDER=imagen
IMAGEN_MODEL=imagen-4.0-fast-generate-001

# Video probing
FFPROBE_PATH=/usr/bin/ffprobe

N8N_PASSWORD=<strong random password>
N8N_ENCRYPTION_KEY=<generate: python -c "import secrets; print(secrets.token_hex(32))">
N8N_HOST=yourdomain.com
N8N_WEBHOOK_URL=https://yourdomain.com/n8n/

# YouTube — direct multi-account OAuth (PostProxy removed)
YOUTUBE_REDIRECT_URI=https://yourdomain.com/api/v1/channels/youtube/callback
```

**Critical:** `APP_ENV=production` enables secure httpOnly cookies (the `secure` flag), HTTPS-only behavior, and disables debug endpoints.

> **Removed in v2 — do not set:** `OPENAI_API_KEY`, `PEXELS_API_KEY`, `PIXABAY_API_KEY`,
> `UNSPLASH_ACCESS_KEY`, `GOOGLE_TTS_API_KEY`, all `REDDIT_*` and `POSTPROXY_*` vars,
> and the old `SMTP_*` block (replaced by Resend).

---

## 5. Domain and SSL Setup

### Point Your Domain

Create an A record pointing `yourdomain.com` (and optionally `www.yourdomain.com`) to your server's IP address. Wait for DNS propagation (typically 5–15 minutes).

### Install Certbot

```bash
sudo apt-get install -y certbot

# Obtain certificate (stop nginx if it's running first)
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com
```

Certbot stores certificates at:
- Certificate: `/etc/letsencrypt/live/yourdomain.com/fullchain.pem`
- Private key: `/etc/letsencrypt/live/yourdomain.com/privkey.pem`

### Enable Auto-Renewal

```bash
# Test renewal
sudo certbot renew --dry-run

# Auto-renewal runs automatically via the certbot systemd timer
# Verify it is active:
sudo systemctl status certbot.timer
```

---

## 6. Nginx SSL Configuration

Update the Nginx virtual host configuration to add HTTPS support.

Open `nginx/conf.d/viralflux.conf` and replace the single server block with:

```nginx
upstream frontend {
    server frontend:3000;
}
upstream backend {
    server backend:8000;
}
upstream n8n {
    server n8n:5678;
}

# HTTP → HTTPS redirect
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate     /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # Modern TLS settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;

    # Security headers
    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;

    client_max_body_size 500M;

    # Gzip
    gzip on;
    gzip_vary on;
    gzip_types text/plain text/css application/json application/javascript;

    # API
    location /api/ {
        proxy_pass         http://backend;
        proxy_http_version 1.1;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_read_timeout 600s;
    }

    # n8n (with WebSocket)
    location /n8n/ {
        proxy_pass         http://n8n;
        proxy_http_version 1.1;
        proxy_set_header   Upgrade           $http_upgrade;
        proxy_set_header   Connection        "upgrade";
        proxy_set_header   Host              $host;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_read_timeout 3600s;
    }

    # Media files
    location /media/ {
        alias /media/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Frontend
    location / {
        proxy_pass         http://frontend;
        proxy_http_version 1.1;
        proxy_set_header   Upgrade           $http_upgrade;
        proxy_set_header   Connection        "upgrade";
        proxy_set_header   Host              $host;
        proxy_set_header   X-Forwarded-Proto $scheme;
    }
}
```

Mount the Let's Encrypt directory into the Nginx container by adding a volume to the `nginx` service in `docker-compose.yml`:

```yaml
nginx:
  image: nginx:1.25-alpine
  ports:
    - "80:80"
    - "443:443"
  volumes:
    - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    - ./nginx/conf.d:/etc/nginx/conf.d:ro
    - ./media:/media:ro
    - /etc/letsencrypt:/etc/letsencrypt:ro   # add this line
```

---

## 7. Firewall Rules (ufw)

```bash
# Enable firewall
sudo ufw enable

# Allow SSH (required — do not skip)
sudo ufw allow OpenSSH

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Deny all other inbound by default (ufw default)
# The application containers communicate internally via the viralflux Docker network

# Verify rules
sudo ufw status verbose
```

**Important:** Do NOT expose ports 5432 (PostgreSQL), 6379 (Redis), 8000 (FastAPI), 3000 (Next.js), or 5678 (n8n) to the public internet. All external access goes through Nginx on ports 80/443.

---

## 8. Start Services

```bash
cd /opt/viralflux
make build    # Build all images (first time only — takes 3–5 minutes)
make up
make ps       # Verify all services are running
```

`make up` starts `backend`, `worker`, and the **`beat`** scheduler (all from the same image), plus `postgres`, `redis`, `frontend`, `n8n`, and `nginx`. The `beat` service is **required** — it runs `scan_schedules` (every 5 min) and `sync_analytics` (daily); without it, scheduled posting and analytics do not run.

Seed the self-hosted CC0 asset libraries (mounted read-only into backend/worker/beat at `/app/assets`) before generating videos:

```bash
bash scripts/seed_music.sh      # music buckets
bash scripts/seed_footage.sh    # footage buckets: satisfying, parkour_clean, hydraulic, kinetic_sand
# drop CC0 .mp3 / .mp4 files into assets/music/<bucket> and assets/footage/<bucket>, then:
docker compose restart worker beat
```

After boot, run `bash scripts/health_check.sh` — it now also verifies the `beat` container is running.

---

## 9. Auto-Start on Server Reboot

Docker containers already restart automatically (`restart: unless-stopped` in docker-compose.yml) as long as the Docker daemon starts on boot, which it does by default on Ubuntu.

Verify Docker starts on boot:

```bash
sudo systemctl is-enabled docker
# Should output: enabled
```

---

## 10. Backup Strategy

### PostgreSQL Data (Critical)

The primary database is stored in the `postgres_data` Docker volume. Back it up with a scheduled pg_dump:

```bash
# Create backup directory
sudo mkdir -p /opt/backups/postgres

# Manual backup
docker exec postgres pg_dump -U viralflux_user viralflux | gzip > /opt/backups/postgres/viralflux_$(date +%Y%m%d_%H%M%S).sql.gz

# Automate with cron (daily at 2 AM, keep 14 days)
crontab -e
```

Add the following cron entries:

```cron
# Backup PostgreSQL daily at 2 AM
0 2 * * * docker exec postgres pg_dump -U viralflux_user viralflux | gzip > /opt/backups/postgres/viralflux_$(date +\%Y\%m\%d).sql.gz

# Delete PostgreSQL backups older than 14 days
30 2 * * * find /opt/backups/postgres -name "*.sql.gz" -mtime +14 -delete
```

### Media Directory (Generated Videos)

The `media/` directory contains all generated MP4 files. Since videos can be re-generated from source data, the media directory is lower priority than the database. However, backing it up avoids the LLM cost of re-generating posted videos.

```bash
# Rsync media to a separate location or object storage
rsync -av /opt/viralflux/media/ user@backup-server:/backups/viralflux/media/

# Or use rclone to sync to S3/Cloudflare R2/Backblaze B2
rclone sync /opt/viralflux/media/ remote:viralflux-media --progress
```

### n8n Workflows

n8n stores its workflow data in the `n8n_data` Docker volume and in the PostgreSQL `n8n` database. The PostgreSQL backup above covers the workflow data. The `n8n/workflows/` directory in the repository also contains JSON exports as a source-of-truth backup.

### Environment Variables

```bash
# Back up the .env file to a secrets manager or encrypted storage
# NEVER commit .env to git
cp /opt/viralflux/.env /secure/backup/viralflux.env
```

---

## 11. Certbot Auto-Renewal with Docker

Since Nginx runs inside Docker, the certbot standalone renewal needs the host's port 80 to be free momentarily. Configure a hook to stop and restart the Nginx container:

```bash
sudo nano /etc/letsencrypt/renewal-hooks/pre/stop-nginx.sh
```

```bash
#!/bin/bash
cd /opt/viralflux
docker compose stop nginx
```

```bash
sudo nano /etc/letsencrypt/renewal-hooks/post/start-nginx.sh
```

```bash
#!/bin/bash
cd /opt/viralflux
docker compose start nginx
```

```bash
sudo chmod +x /etc/letsencrypt/renewal-hooks/pre/stop-nginx.sh
sudo chmod +x /etc/letsencrypt/renewal-hooks/post/start-nginx.sh
```

---

## 12. Monitoring

### Check Service Health

```bash
# View all container statuses
make ps

# Follow all logs
make logs

# Follow only the backend
docker compose logs -f backend

# Follow the worker and the beat scheduler
make logs-worker
make logs-beat

# Check Celery worker queue
docker compose exec backend celery -A app.workers.celery_app inspect active

# Confirm the beat scheduler is registering its periodic tasks
docker compose logs beat | grep -E "scan_schedules|sync_analytics"
```

### Check Resource Usage

```bash
# Live resource usage per container
docker stats

# Disk usage
df -h /
du -sh /opt/viralflux/media/
```

### Alert on High CPU/Memory (optional)

Install `netdata` for real-time monitoring with web UI:

```bash
bash <(curl -Ss https://my-netdata.io/kickstart.sh) --dont-start-it
# Configure to listen on localhost only, access via SSH tunnel
```

---

## 13. Common Production Issues

**Port 443 not accessible**
Ensure ufw allows port 443 (`sudo ufw allow 443/tcp`) and the `nginx` service in docker-compose.yml maps `"443:443"`.

**Let's Encrypt certificate not found inside Nginx container**
Verify the `/etc/letsencrypt` volume mount is in docker-compose.yml for the nginx service and that the path in `ssl_certificate` matches the actual certbot output path.

**Celery worker not processing jobs**
Check `make logs-worker`. Common causes: Redis connection issue (wrong `CELERY_BROKER_URL`), or a task import error (check Python tracebacks in the log).

**Scheduled posts / analytics never run**
The `beat` service is the scheduler. Check `make logs-beat` — you should see `scan_schedules` ticking every 5 minutes and `sync_analytics` daily. If `beat` is missing from `make ps`, it failed to start (same image as backend — check the same env/import errors). n8n is only a supplementary nudge and cannot substitute for `beat`.

**YouTube OAuth callback fails in production**
The `YOUTUBE_REDIRECT_URI` in `.env` must exactly match the URI registered in Google Cloud Console. After changing the URL or domain, update both places.

**Out of disk space**
The `media/` directory fills up with generated videos. Set a cron to remove videos older than 30 days for jobs that have already been posted:

```bash
# Remove posted video files older than 30 days (keep DB records)
find /opt/viralflux/media/ -name "*.mp4" -mtime +30 -delete
```

Adjust the retention period based on your available disk and user expectations.
