"""CC0 "satisfying loop" footage library for ViralFlux.

Used by the BRAINROT visual path (``visual == "loop_footage"``): instead of
generating images, the pipeline picks a random CC0 background loop (satisfying
hydraulic-press / parkour / kinetic-sand style clips) to play under the
narration + captions.

Directory structure expected::

    {assets_dir}/footage/{bucket}/{loop1}.mp4
                                  {loop2}.mp4
                                  …

Buckets (see scaffold READMEs): satisfying, parkour_clean, hydraulic, kinetic_sand.

Mirrors :class:`app.services.assets.music_library.MusicLibrary` in style.
"""
from __future__ import annotations

import logging
import os
import random

logger = logging.getLogger(__name__)

# Video container extensions we treat as loopable footage.
_VIDEO_EXTENSIONS = (".mp4", ".mov", ".webm", ".mkv")


class FootageLibrary:
    """Random selector for CC0 loop footage backed by a local assets directory."""

    def __init__(self, assets_dir: str) -> None:
        self.assets_dir = assets_dir

    def pick_loop(self, bucket: str, min_seconds: float = 0.0) -> str | None:
        """Return a random local loop path from ``bucket`` at least ``min_seconds`` long.

        Probing duration requires ffprobe; if ffprobe is unavailable or fails for
        a candidate, that candidate is treated as duration-unknown and only used
        when no length filter is requested (``min_seconds <= 0``).

        Returns None if the bucket directory is missing, empty, or no clip is long
        enough.
        """
        bucket_dir = os.path.join(self.assets_dir, "footage", bucket)
        if not os.path.isdir(bucket_dir):
            logger.warning("Footage bucket directory not found: %s", bucket_dir)
            return None

        clips = [
            f
            for f in os.listdir(bucket_dir)
            if f.lower().endswith(_VIDEO_EXTENSIONS)
        ]
        if not clips:
            logger.warning("No loop clips found in %s", bucket_dir)
            return None

        random.shuffle(clips)

        if min_seconds <= 0:
            chosen = os.path.join(bucket_dir, clips[0])
            logger.debug("Selected loop (no length filter): %s", chosen)
            return chosen

        for clip in clips:
            full_path = os.path.join(bucket_dir, clip)
            duration = self._probe_duration(full_path)
            if duration is not None and duration >= min_seconds:
                logger.debug(
                    "Selected loop %s (%.1fs >= %.1fs)", full_path, duration, min_seconds
                )
                return full_path

        logger.warning(
            "No loop in bucket '%s' is at least %.1fs long.", bucket, min_seconds
        )
        return None

    def list_buckets(self) -> list[str]:
        """Return the list of available footage bucket names."""
        footage_root = os.path.join(self.assets_dir, "footage")
        if not os.path.isdir(footage_root):
            return []
        return [
            d
            for d in os.listdir(footage_root)
            if os.path.isdir(os.path.join(footage_root, d))
        ]

    @staticmethod
    def _probe_duration(path: str) -> float | None:
        """Return the duration of ``path`` in seconds via ffprobe, or None on failure."""
        import subprocess

        from app.core.config import settings

        try:
            result = subprocess.run(
                [
                    settings.FFPROBE_PATH,
                    "-v",
                    "error",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "default=noprint_wrappers=1:nokey=1",
                    path,
                ],
                capture_output=True,
                text=True,
                timeout=15,
            )
            if result.returncode != 0:
                logger.debug("ffprobe failed for %s: %s", path, result.stderr.strip())
                return None
            return float(result.stdout.strip())
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            logger.debug("Could not probe duration for %s: %s", path, exc)
            return None


# Module-level singleton, configured from settings.
from app.core.config import settings  # noqa: E402  (placed after class def, mirrors usage)

footage_library = FootageLibrary(settings.ASSETS_DIR)
