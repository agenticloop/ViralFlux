from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)

_PIXABAY_BASE = "https://pixabay.com/api/"
_DOWNLOAD_TIMEOUT = 30  # seconds


class PixabayError(Exception):
    """Raised when a Pixabay API request fails."""


class PixabayService:
    """Client for the Pixabay photo search API.

    Used as a fallback when Pexels is unavailable or returns no results.
    """

    def __init__(self, api_key: str) -> None:
        if not api_key:
            raise PixabayError(
                "Pixabay API key is not set. "
                "Set PIXABAY_API_KEY in your .env file."
            )
        self._api_key = api_key

    async def search_photos(
        self,
        query: str,
        count: int = 5,
    ) -> list[str]:
        """Search Pixabay for photos matching query.

        Returns a list of direct image URLs (largest available size).
        Filters to photo type and vertical orientation where possible.
        """
        params = {
            "key": self._api_key,
            "q": query,
            "image_type": "photo",
            "orientation": "vertical",
            "per_page": min(count, 200),  # Pixabay max per_page = 200
            "safesearch": "true",
            "order": "popular",
        }

        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(_PIXABAY_BASE, params=params)

        if response.status_code != 200:
            raise PixabayError(
                f"Pixabay API returned HTTP {response.status_code}: {response.text[:300]}"
            )

        data = response.json()
        hits = data.get("hits", [])
        if not hits:
            logger.warning("Pixabay returned 0 results for query: '%s'", query)
            return []

        urls: list[str] = []
        for hit in hits[:count]:
            # Prefer largest available image
            url = (
                hit.get("largeImageURL")
                or hit.get("webformatURL")
                or hit.get("previewURL")
            )
            if url:
                urls.append(url)

        return urls

    async def download(self, url: str, path: str) -> str:
        """Download an image from url and save it to path. Returns path."""
        async with httpx.AsyncClient(timeout=_DOWNLOAD_TIMEOUT) as client:
            response = await client.get(url, follow_redirects=True)

        if response.status_code != 200:
            raise PixabayError(
                f"Failed to download image from {url}: HTTP {response.status_code}"
            )

        with open(path, "wb") as f:
            f.write(response.content)

        logger.debug("Downloaded %d bytes → %s", len(response.content), path)
        return path
