from __future__ import annotations

import logging
import os

from .pexels import PexelsService, PexelsError
from .pixabay import PixabayService, PixabayError
from .music_library import MusicLibrary

logger = logging.getLogger(__name__)


async def fetch_images(
    keywords: list[str],
    count: int,
    output_dir: str,
    pexels_key: str,
    pixabay_key: str,
) -> list[str]:
    """Fetch stock images for the given keywords.

    Strategy:
    1. Try Pexels first with a horror-styled query.
    2. Fall back to Pixabay if Pexels fails or returns no images.

    Returns a list of local file paths for the downloaded images.
    """
    query = " ".join(keywords[:3]) + " dark atmospheric horror"
    os.makedirs(output_dir, exist_ok=True)

    # --- Pexels attempt ---
    if pexels_key:
        try:
            pexels = PexelsService(pexels_key)
            urls = await pexels.search_photos(query, count)
            paths: list[str] = []
            for i, url in enumerate(urls):
                path = os.path.join(output_dir, f"img_{i}.jpg")
                await pexels.download(url, path)
                paths.append(path)
            if paths:
                logger.info("Fetched %d images from Pexels for query '%s'", len(paths), query)
                return paths
        except (PexelsError, Exception) as exc:
            logger.warning("Pexels fetch failed (%s); falling back to Pixabay.", exc)

    # --- Pixabay fallback ---
    if not pixabay_key:
        logger.error("No Pixabay API key set and Pexels failed — returning empty image list.")
        return []

    pixabay = PixabayService(pixabay_key)
    urls = await pixabay.search_photos(query, count)
    paths = []
    for i, url in enumerate(urls):
        path = os.path.join(output_dir, f"img_{i}.jpg")
        await pixabay.download(url, path)
        paths.append(path)

    logger.info("Fetched %d images from Pixabay for query '%s'", len(paths), query)
    return paths


__all__ = [
    "PexelsService",
    "PexelsError",
    "PixabayService",
    "PixabayError",
    "MusicLibrary",
    "fetch_images",
]
