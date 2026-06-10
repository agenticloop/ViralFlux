from __future__ import annotations

import logging
from typing import Any

from google.oauth2.credentials import Credentials
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
]

_GOOGLE_AUTH_URI = "https://accounts.google.com/o/oauth2/auth"
_GOOGLE_TOKEN_URI = "https://oauth2.googleapis.com/token"


class YouTubeServiceError(Exception):
    """Raised when a YouTube API operation fails."""


class YouTubeService:
    """Google YouTube Data API v3 service wrapper."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
    ) -> None:
        if not client_id or not client_secret:
            raise YouTubeServiceError(
                "YouTube OAuth credentials (client_id, client_secret) are not set."
            )
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    # ------------------------------------------------------------------
    # OAuth helpers
    # ------------------------------------------------------------------

    def _make_flow(self) -> Flow:
        """Build a google_auth_oauthlib Flow instance."""
        client_config = {
            "web": {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uris": [self.redirect_uri],
                "auth_uri": _GOOGLE_AUTH_URI,
                "token_uri": _GOOGLE_TOKEN_URI,
            }
        }
        flow = Flow.from_client_config(
            client_config,
            scopes=SCOPES,
            redirect_uri=self.redirect_uri,
        )
        return flow

    def get_auth_url(self, state: str) -> str:
        """Return the Google OAuth consent-screen URL.

        The user should be redirected here to grant YouTube permissions.
        ``state`` is an opaque value that will be returned in the callback.
        """
        flow = self._make_flow()
        url, _returned_state = flow.authorization_url(
            state=state,
            access_type="offline",
            prompt="consent",
            include_granted_scopes="true",
        )
        return url

    def exchange_code(self, code: str) -> dict:
        """Exchange an OAuth authorisation code for access / refresh tokens.

        Returns:
            {
                "access_token": str,
                "refresh_token": str,
                "expiry": str  (ISO-8601 datetime string or empty)
            }
        """
        flow = self._make_flow()
        try:
            flow.fetch_token(code=code)
        except Exception as exc:
            raise YouTubeServiceError(
                f"Failed to exchange OAuth code for tokens: {exc}"
            ) from exc

        credentials = flow.credentials
        expiry_str = (
            credentials.expiry.isoformat() if credentials.expiry else ""
        )
        return {
            "access_token": credentials.token,
            "refresh_token": credentials.refresh_token or "",
            "expiry": expiry_str,
        }

    def refresh_access_token(self, refresh_token: str) -> dict:
        """Use a refresh token to obtain a new access token.

        Returns:
            {
                "access_token": str,
                "expiry": str
            }
        """
        import google.auth.transport.requests as google_requests
        import requests as std_requests

        credentials = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri=_GOOGLE_TOKEN_URI,
            client_id=self.client_id,
            client_secret=self.client_secret,
        )
        request = google_requests.Request(session=std_requests.Session())
        try:
            credentials.refresh(request)
        except Exception as exc:
            raise YouTubeServiceError(
                f"Failed to refresh access token: {exc}"
            ) from exc

        expiry_str = credentials.expiry.isoformat() if credentials.expiry else ""
        return {
            "access_token": credentials.token,
            "expiry": expiry_str,
        }

    def _build_youtube_client(self, access_token: str, refresh_token: str):
        """Build an authenticated YouTube API client."""
        credentials = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri=_GOOGLE_TOKEN_URI,
            client_id=self.client_id,
            client_secret=self.client_secret,
            scopes=SCOPES,
        )
        return build("youtube", "v3", credentials=credentials, cache_discovery=False)

    # ------------------------------------------------------------------
    # Video upload
    # ------------------------------------------------------------------

    async def upload_video(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: list[str],
        access_token: str,
        refresh_token: str,
        scheduled_time: str | None = None,
    ) -> str:
        """Upload a video to YouTube via resumable upload.

        If ``scheduled_time`` is provided (ISO-8601), the video is uploaded as
        private with a scheduled publish time. Otherwise it goes public immediately.

        Returns the YouTube video_id string.
        """
        import asyncio

        loop = asyncio.get_running_loop()
        video_id = await loop.run_in_executor(
            None,
            self._upload_video_sync,
            video_path,
            title,
            description,
            tags,
            access_token,
            refresh_token,
            scheduled_time,
        )
        return video_id

    def _upload_video_sync(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: list[str],
        access_token: str,
        refresh_token: str,
        scheduled_time: str | None,
    ) -> str:
        """Blocking upload — runs inside a thread executor."""
        youtube = self._build_youtube_client(access_token, refresh_token)

        if scheduled_time:
            privacy_status = "private"
            status_body: dict[str, Any] = {
                "privacyStatus": privacy_status,
                "publishAt": scheduled_time,
                "selfDeclaredMadeForKids": False,
            }
        else:
            status_body = {
                "privacyStatus": "public",
                "selfDeclaredMadeForKids": False,
            }

        body = {
            "snippet": {
                "title": title[:100],
                "description": description[:5000],
                "tags": tags[:500],
                "categoryId": "22",  # People & Blogs
            },
            "status": status_body,
        }

        media = MediaFileUpload(
            video_path,
            mimetype="video/mp4",
            resumable=True,
            chunksize=8 * 1024 * 1024,  # 8 MB chunks
        )

        try:
            request = youtube.videos().insert(
                part="snippet,status",
                body=body,
                media_body=media,
            )
            response = None
            while response is None:
                _status, response = request.next_chunk()
                if _status:
                    logger.debug(
                        "YouTube upload progress: %.0f%%",
                        _status.progress() * 100,
                    )
        except Exception as exc:
            raise YouTubeServiceError(
                f"YouTube video upload failed: {exc}"
            ) from exc

        video_id: str = response.get("id", "")
        logger.info("YouTube upload complete. video_id=%s", video_id)
        return video_id

    # ------------------------------------------------------------------
    # Analytics
    # ------------------------------------------------------------------

    async def get_video_stats(
        self,
        video_id: str,
        access_token: str,
    ) -> dict:
        """Fetch basic statistics for a video (views, likes, comments).

        Returns a dict with integer values for each metric.
        """
        import asyncio

        loop = asyncio.get_running_loop()
        stats = await loop.run_in_executor(
            None,
            self._get_video_stats_sync,
            video_id,
            access_token,
        )
        return stats

    def _get_video_stats_sync(self, video_id: str, access_token: str) -> dict:
        """Blocking stats fetch — runs inside a thread executor."""
        credentials = Credentials(token=access_token)
        youtube = build("youtube", "v3", credentials=credentials, cache_discovery=False)

        try:
            response = (
                youtube.videos()
                .list(part="statistics", id=video_id)
                .execute()
            )
        except Exception as exc:
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
            "favorites": int(raw.get("favoriteCount", 0)),
        }
