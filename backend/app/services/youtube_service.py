from __future__ import annotations

import asyncio
import logging
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)

# OAuth scopes requested per channel. ``userinfo.email`` + ``openid`` let us
# read which Google account authorised the channel; ``youtube.upload`` and
# ``youtube.readonly`` cover publishing + stats.
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid",
]

_GOOGLE_AUTH_URI = "https://accounts.google.com/o/oauth2/auth"
_GOOGLE_TOKEN_URI = "https://oauth2.googleapis.com/token"
_USERINFO_URI = "https://www.googleapis.com/oauth2/v3/userinfo"

# Network timeout (seconds) for token/userinfo HTTP calls.
_HTTP_TIMEOUT = 30


class YouTubeServiceError(Exception):
    """Raised when a YouTube API operation fails."""


class YouTubeService:
    """Direct, multi-account Google OAuth wrapper for the YouTube Data API v3.

    OAuth is performed *per channel*: each connected channel may live under a
    different Google account, so each channel stores its own encrypted tokens
    and ``google_account_email``. This service only deals with the Google side
    (building consent URLs, exchanging codes, refreshing tokens, uploading and
    reading stats); persisting the resulting tokens onto the ``YoutubeChannel``
    row is the caller's job.

    The service degrades gracefully when OAuth credentials are unset: it can be
    instantiated, but any operation that needs Google will raise a clear
    :class:`RuntimeError`. This keeps the app importable/bootable with the
    placeholder env values.
    """

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        redirect_uri: str | None = None,
    ) -> None:
        self.client_id = client_id if client_id is not None else settings.YOUTUBE_CLIENT_ID
        self.client_secret = (
            client_secret if client_secret is not None else settings.YOUTUBE_CLIENT_SECRET
        )
        self.redirect_uri = (
            redirect_uri if redirect_uri is not None else settings.YOUTUBE_REDIRECT_URI
        )

    # ------------------------------------------------------------------
    # Credential guards / lazy imports
    # ------------------------------------------------------------------

    @staticmethod
    def _is_real(value: str | None) -> bool:
        """A credential counts as set only if it's non-blank and not a placeholder.

        Lets the app ship with empty / ``REPLACE_ME*`` env values and stay
        cleanly 'not configured' until real keys are dropped in — at which point
        OAuth auto-enables with no code change.
        """
        v = (value or "").strip()
        return bool(v) and not v.upper().startswith("REPLACE_ME")

    @property
    def configured(self) -> bool:
        """True when real OAuth client credentials are present."""
        return self._is_real(self.client_id) and self._is_real(self.client_secret)

    def _require_credentials(self) -> None:
        if not self.configured:
            raise RuntimeError(
                "YouTube OAuth is not configured. Set YOUTUBE_CLIENT_ID and "
                "YOUTUBE_CLIENT_SECRET to enable channel connection and uploads."
            )

    def _client_config(self) -> dict[str, Any]:
        return {
            "web": {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uris": [self.redirect_uri],
                "auth_uri": _GOOGLE_AUTH_URI,
                "token_uri": _GOOGLE_TOKEN_URI,
            }
        }

    def _make_flow(self, state: str | None = None):
        """Build a google_auth_oauthlib ``Flow`` (imported lazily)."""
        from google_auth_oauthlib.flow import Flow

        flow = Flow.from_client_config(
            self._client_config(),
            scopes=SCOPES,
            redirect_uri=self.redirect_uri,
        )
        if state is not None:
            flow.state = state
        return flow

    def _credentials(self, access_token: str | None, refresh_token: str | None):
        """Build a google.oauth2 Credentials object (imported lazily)."""
        from google.oauth2.credentials import Credentials

        return Credentials(
            token=access_token or None,
            refresh_token=refresh_token or None,
            token_uri=_GOOGLE_TOKEN_URI,
            client_id=self.client_id,
            client_secret=self.client_secret,
            scopes=SCOPES,
        )

    def _build_youtube_client(self, credentials):
        from googleapiclient.discovery import build

        return build(
            "youtube",
            "v3",
            credentials=credentials,
            cache_discovery=False,
        )

    # ------------------------------------------------------------------
    # OAuth: consent URL
    # ------------------------------------------------------------------

    def get_auth_url(self, channel_id: str, state: str) -> str:
        """Return the Google OAuth consent-screen URL for connecting a channel.

        ``state`` is an opaque value (encodes ``channel_id``) round-tripped back
        to the callback so we know which channel row to attach tokens to.
        ``channel_id`` is accepted for symmetry/logging; callers should encode
        it into ``state`` themselves and store ``state`` on the channel row.
        """
        self._require_credentials()
        flow = self._make_flow(state=state)
        url, _returned_state = flow.authorization_url(
            access_type="offline",
            prompt="consent",
            include_granted_scopes="true",
            state=state,
        )
        logger.debug("Built YouTube OAuth URL for channel=%s", channel_id)
        return url

    # ------------------------------------------------------------------
    # OAuth: code exchange
    # ------------------------------------------------------------------

    async def exchange_code(self, code: str) -> dict:
        """Exchange an OAuth authorisation ``code`` for tokens + channel info.

        Returns (all string values, ``expiry`` ISO-8601 or empty)::

            {
                "access_token":  str,   # plaintext — caller encrypts
                "refresh_token": str,   # plaintext — caller encrypts
                "expiry":        str,   # ISO-8601 UTC datetime or ""
                "channel_id":    str,   # YouTube channel id
                "channel_title": str,
                "thumbnail_url": str,
                "email":         str,   # Google account email
            }
        """
        self._require_credentials()
        return await asyncio.to_thread(self._exchange_code_sync, code)

    def _exchange_code_sync(self, code: str) -> dict:
        flow = self._make_flow()
        try:
            flow.fetch_token(code=code)
        except Exception as exc:  # noqa: BLE001 - surface a clean error
            raise YouTubeServiceError(
                f"Failed to exchange OAuth code for tokens: {exc}"
            ) from exc

        credentials = flow.credentials
        expiry_str = credentials.expiry.isoformat() if credentials.expiry else ""

        email = self._fetch_userinfo_email(credentials)
        channel = self._fetch_my_channel(credentials)

        return {
            "access_token": credentials.token or "",
            "refresh_token": credentials.refresh_token or "",
            "expiry": expiry_str,
            "channel_id": channel.get("channel_id", ""),
            "channel_title": channel.get("channel_title", ""),
            "thumbnail_url": channel.get("thumbnail_url", ""),
            "email": email,
        }

    def _fetch_userinfo_email(self, credentials) -> str:
        """Read the Google account email via the userinfo endpoint."""
        from google.auth.transport.requests import AuthorizedSession

        try:
            session = AuthorizedSession(credentials)
            resp = session.get(_USERINFO_URI, timeout=_HTTP_TIMEOUT)
            resp.raise_for_status()
            return resp.json().get("email", "") or ""
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to fetch Google userinfo email: %s", exc)
            return ""

    def _fetch_my_channel(self, credentials) -> dict:
        """Fetch the authorising account's own channel (id/title/thumbnail)."""
        try:
            youtube = self._build_youtube_client(credentials)
            response = (
                youtube.channels()
                .list(part="snippet", mine=True)
                .execute()
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to fetch connected YouTube channel: %s", exc)
            return {}

        items = response.get("items", [])
        if not items:
            logger.warning("Authorised Google account has no YouTube channel.")
            return {}

        item = items[0]
        snippet = item.get("snippet", {})
        thumbnails = snippet.get("thumbnails", {})
        # Prefer the highest-resolution thumbnail available.
        thumb = (
            thumbnails.get("high")
            or thumbnails.get("medium")
            or thumbnails.get("default")
            or {}
        )
        return {
            "channel_id": item.get("id", ""),
            "channel_title": snippet.get("title", ""),
            "thumbnail_url": thumb.get("url", ""),
        }

    # ------------------------------------------------------------------
    # OAuth: refresh
    # ------------------------------------------------------------------

    async def refresh_access_token(self, refresh_token: str) -> dict:
        """Use a refresh token to mint a fresh access token.

        Returns ``{"access_token": str, "expiry": str}`` (expiry ISO-8601 or "").
        """
        self._require_credentials()
        if not refresh_token:
            raise YouTubeServiceError("Cannot refresh: no refresh_token provided.")
        return await asyncio.to_thread(self._refresh_access_token_sync, refresh_token)

    def _refresh_access_token_sync(self, refresh_token: str) -> dict:
        import google.auth.transport.requests as google_requests
        import requests as std_requests

        credentials = self._credentials(access_token=None, refresh_token=refresh_token)
        request = google_requests.Request(session=std_requests.Session())
        try:
            credentials.refresh(request)
        except Exception as exc:  # noqa: BLE001
            raise YouTubeServiceError(
                f"Failed to refresh access token: {exc}"
            ) from exc

        expiry_str = credentials.expiry.isoformat() if credentials.expiry else ""
        return {
            "access_token": credentials.token or "",
            "expiry": expiry_str,
        }

    # ------------------------------------------------------------------
    # Internal: authenticated client with auto-refresh
    # ------------------------------------------------------------------

    def _authed_client(self, access_token: str, refresh_token: str):
        """Build a YouTube client whose credentials auto-refresh on expiry.

        google-api-python-client transparently refreshes the access token when
        it is expired *and* a refresh token + client secret are present, so we
        just hand it a Credentials object carrying both.
        """
        credentials = self._credentials(access_token, refresh_token)
        return self._build_youtube_client(credentials)

    # ------------------------------------------------------------------
    # Video upload
    # ------------------------------------------------------------------

    async def upload_video(
        self,
        access_token: str,
        refresh_token: str,
        file_path: str,
        title: str,
        description: str,
        tags: list[str] | None = None,
        privacy: str = "public",
    ) -> dict:
        """Resumable upload of a video to YouTube.

        Runs the blocking google-api-python-client upload in a thread. The
        underlying credentials auto-refresh if the access token is expired.

        Returns ``{"video_id": str, "url": str}``.
        """
        self._require_credentials()
        return await asyncio.to_thread(
            self._upload_video_sync,
            access_token,
            refresh_token,
            file_path,
            title,
            description,
            tags or [],
            privacy,
        )

    def _upload_video_sync(
        self,
        access_token: str,
        refresh_token: str,
        file_path: str,
        title: str,
        description: str,
        tags: list[str],
        privacy: str,
    ) -> dict:
        from googleapiclient.http import MediaFileUpload

        privacy_status = privacy if privacy in {"public", "private", "unlisted"} else "public"
        body = {
            "snippet": {
                "title": title[:100],
                "description": description[:5000],
                "tags": tags[:500],
                "categoryId": "22",  # People & Blogs
            },
            "status": {
                "privacyStatus": privacy_status,
                "selfDeclaredMadeForKids": False,
            },
        }

        media = MediaFileUpload(
            file_path,
            mimetype="video/mp4",
            resumable=True,
            chunksize=8 * 1024 * 1024,  # 8 MB chunks
        )

        try:
            youtube = self._authed_client(access_token, refresh_token)
            request = youtube.videos().insert(
                part="snippet,status",
                body=body,
                media_body=media,
            )
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    logger.debug(
                        "YouTube upload progress: %.0f%%", status.progress() * 100
                    )
        except Exception as exc:  # noqa: BLE001
            raise YouTubeServiceError(f"YouTube video upload failed: {exc}") from exc

        video_id: str = response.get("id", "")
        if not video_id:
            raise YouTubeServiceError("YouTube upload returned no video id.")
        logger.info("YouTube upload complete. video_id=%s", video_id)
        return {
            "video_id": video_id,
            "url": f"https://www.youtube.com/watch?v={video_id}",
        }

    # ------------------------------------------------------------------
    # Analytics
    # ------------------------------------------------------------------

    async def get_video_stats(
        self,
        access_token: str,
        refresh_token: str,
        video_id: str,
    ) -> dict:
        """Fetch basic statistics for a video.

        Returns ``{"views": int, "likes": int, "comments": int}``. Credentials
        auto-refresh if the access token is expired.
        """
        self._require_credentials()
        return await asyncio.to_thread(
            self._get_video_stats_sync,
            access_token,
            refresh_token,
            video_id,
        )

    def _get_video_stats_sync(
        self,
        access_token: str,
        refresh_token: str,
        video_id: str,
    ) -> dict:
        try:
            youtube = self._authed_client(access_token, refresh_token)
            response = (
                youtube.videos()
                .list(part="statistics", id=video_id)
                .execute()
            )
        except Exception as exc:  # noqa: BLE001
            raise YouTubeServiceError(
                f"Failed to fetch stats for video {video_id}: {exc}"
            ) from exc

        items = response.get("items", [])
        if not items:
            raise YouTubeServiceError(
                f"Video {video_id} not found or not accessible."
            )

        raw = items[0].get("statistics", {})
        return {
            "views": int(raw.get("viewCount", 0)),
            "likes": int(raw.get("likeCount", 0)),
            "comments": int(raw.get("commentCount", 0)),
        }


# Module-level singleton — safe to import even when creds are placeholders.
youtube_service = YouTubeService()
