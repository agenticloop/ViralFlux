from __future__ import annotations

import logging
import os
import random

logger = logging.getLogger(__name__)


class MusicLibrary:
    """Simple music track selector backed by a local assets directory.

    Directory structure expected:
        {assets_dir}/music/{category}/{track1}.mp3
                                      {track2}.mp3
                                      …
    """

    def __init__(self, assets_dir: str) -> None:
        self.assets_dir = assets_dir

    def get_track(self, category: str) -> str | None:
        """Return a randomly selected .mp3 path from the given category directory.

        Returns None if the directory does not exist or contains no .mp3 files.
        """
        music_dir = os.path.join(self.assets_dir, "music", category)
        if not os.path.isdir(music_dir):
            logger.warning(
                "Music category directory not found: %s", music_dir
            )
            return None

        tracks = [
            f for f in os.listdir(music_dir) if f.lower().endswith(".mp3")
        ]
        if not tracks:
            logger.warning("No .mp3 tracks found in %s", music_dir)
            return None

        chosen = random.choice(tracks)
        full_path = os.path.join(music_dir, chosen)
        logger.debug("Selected music track: %s", full_path)
        return full_path

    def list_categories(self) -> list[str]:
        """Return the list of available music category names."""
        music_root = os.path.join(self.assets_dir, "music")
        if not os.path.isdir(music_root):
            return []
        return [
            d
            for d in os.listdir(music_root)
            if os.path.isdir(os.path.join(music_root, d))
        ]
