from __future__ import annotations

import logging
from pathlib import Path

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_BASE = "https://api.postproxy.dev/api"


class PostProxyError(Exception):
    pass


class PostProxyService:
    """PostProxy.dev wrapper for YouTube auto-posting."""

    def _headers(self) -> dict:
        if not settings.POSTPROXY_API_KEY:
            raise PostProxyError("POSTPROXY_API_KEY is not set.")
        return {"Authorization": f"Bearer {settings.POSTPROXY_API_KEY}"}

    # ------------------------------------------------------------------
    # Profile management
    # ------------------------------------------------------------------

    async def list_profile_groups(self) -> list[dict]:
        """Return all profile groups on the account."""
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(f"{_BASE}/profile_groups", headers=self._headers())
        self._raise_for_status(resp, "list_profile_groups")
        data = resp.json()
        return data.get("profile_groups", data) if isinstance(data, dict) else data

    async def list_profiles(self, platform: str = "youtube") -> list[dict]:
        """Return connected social profiles, optionally filtered by platform."""
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(f"{_BASE}/profiles", headers=self._headers())
        self._raise_for_status(resp, "list_profiles")
        data = resp.json()
        profiles = data.get("profiles", data) if isinstance(data, dict) else data
        if platform:
            profiles = [p for p in profiles if p.get("platform") == platform]
        return profiles

    async def initialize_connection(
        self, profile_group_id: str, redirect_url: str
    ) -> dict:
        """Start a PostProxy OAuth flow for YouTube.

        Returns {"url": "<google-oauth-url>", "connection_id": "conn_..."}
        """
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{_BASE}/profile_groups/{profile_group_id}/initialize_connection",
                headers=self._headers(),
                json={"platform": "youtube", "redirect_url": redirect_url},
            )
        self._raise_for_status(resp, "initialize_connection")
        return resp.json()

    # ------------------------------------------------------------------
    # Posting
    # ------------------------------------------------------------------

    async def upload_video(
        self,
        profile_id: str,
        video_path: str,
        title: str,
        description: str,
        tags: list[str],
        scheduled_at: str | None = None,
        privacy_status: str = "public",
    ) -> str:
        """Upload a video file to YouTube via PostProxy.

        Returns the PostProxy post ID (use get_post() to poll for status).
        """
        path = Path(video_path)
        if not path.exists():
            raise PostProxyError(f"Video file not found: {video_path}")

        tag_str = ",".join(tags[:50]) if tags else ""
        fields = {
            "post[body]": description[:5000],
            "profiles[]": profile_id,
            "platforms[youtube][title]": title[:100],
            "platforms[youtube][privacy_status]": privacy_status,
            "platforms[youtube][made_for_kids]": "false",
        }
        if tag_str:
            fields["platforms[youtube][tags]"] = tag_str
        if scheduled_at:
            fields["post[scheduled_at]"] = scheduled_at

        with open(path, "rb") as f:
            async with httpx.AsyncClient(timeout=300) as client:
                resp = await client.post(
                    f"{_BASE}/posts",
                    headers=self._headers(),
                    data=fields,
                    files={"media[]": (path.name, f, "video/mp4")},
                )
        self._raise_for_status(resp, "upload_video")
        data = resp.json()
        post_id = data.get("id") or data.get("post", {}).get("id", "")
        logger.info("PostProxy post created: id=%s profile=%s", post_id, profile_id)
        return str(post_id)

    async def get_post(self, post_id: str) -> dict:
        """Fetch post details and per-platform publish status."""
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                f"{_BASE}/posts/{post_id}", headers=self._headers()
            )
        self._raise_for_status(resp, "get_post")
        return resp.json()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _raise_for_status(self, resp: httpx.Response, op: str) -> None:
        if resp.status_code not in (200, 201):
            logger.error("PostProxy %s failed %s: %s", op, resp.status_code, resp.text)
            raise PostProxyError(
                f"PostProxy {op} failed ({resp.status_code}): {resp.text}"
            )
