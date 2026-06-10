from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)

_PEXELS_BASE = "https://api.pexels.com/v1"
_DOWNLOAD_TIMEOUT = 30  # seconds


class PexelsError(Exception):
    """Raised when a Pexels API request fails."""


class PexelsService:
    """Client for the Pexels photo search API."""

    def __init__(self, api_key: str) -> None:
        if not api_key:
            raise PexelsError(
                "Pexels API key is not set. "
                "Set PEXELS_API_KEY in your .env file."
            )
        self._api_key = api_key

    async def search_photos(
        self,
        query: str,
        count: int = 5,
    ) -> list[str]:
        """Search Pexels for photos matching query.

        Returns a list of direct image URLs (original resolution, portrait
        orientation preferred for 9:16 Shorts).
        """
        params = {
            "query": query,
            "per_page": count,
            "orientation": "portrait",
        }
        headers = {"Authorization": self._api_key}

        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(
                f"{_PEXELS_BASE}/search",
                params=params,
                headers=headers,
            )

        if response.status_code != 200:
            raise PexelsError(
                f"Pexels API returned HTTP {response.status_code}: {response.text[:300]}"
            )

        data = response.json()
        photos = data.get("photos", [])
        if not photos:
            logger.warning("Pexels returned 0 results for query: '%s'", query)
            return []

        urls: list[str] = []
        for photo in photos:
            src = photo.get("src", {})
            url = src.get("original") or src.get("large2x") or src.get("large")
            if url:
                urls.append(url)

        return urls

    async def download(self, url: str, path: str) -> str:
        """Download an image from url and save it to path. Returns path."""
        async with httpx.AsyncClient(timeout=_DOWNLOAD_TIMEOUT) as client:
            response = await client.get(url, follow_redirects=True)

        if response.status_code != 200:
            raise PexelsError(
                f"Failed to download image from {url}: HTTP {response.status_code}"
            )

        with open(path, "wb") as f:
            f.write(response.content)

        logger.debug("Downloaded %d bytes → %s", len(response.content), path)
        return path
