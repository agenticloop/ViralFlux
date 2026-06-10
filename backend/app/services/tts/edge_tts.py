from __future__ import annotations

import asyncio
import json
import logging
import subprocess

import edge_tts

from .base import TTSService, TTSResult

logger = logging.getLogger(__name__)

DEFAULT_VOICE = "en-US-GuyNeural"


class TTSError(Exception):
    """Raised when a TTS synthesis operation fails."""


class EdgeTTSService(TTSService):
    """Free Microsoft Edge TTS via the edge-tts package."""

    provider = "edge-tts"

    @property
    def cost_per_char(self) -> float:
        return 0.0

    async def synthesize(self, text: str, voice_id: str, output_path: str) -> TTSResult:
        """Synthesise text to speech and save to output_path (.mp3).

        Falls back to DEFAULT_VOICE if voice_id is empty or None.
        """
        voice = voice_id or DEFAULT_VOICE

        if not text.strip():
            raise TTSError("Cannot synthesise empty text.")

        communicate = edge_tts.Communicate(text, voice)
        try:
            await communicate.save(output_path)
        except Exception as exc:
            logger.exception("edge-tts synthesis failed for voice %s", voice)
            raise TTSError(f"edge-tts synthesis failed: {exc}") from exc

        duration = _get_duration_ffprobe(output_path)
        return TTSResult(
            audio_path=output_path,
            duration_sec=duration,
            char_count=len(text),
        )


def _get_duration_ffprobe(path: str) -> float:
    """Return duration in seconds via ffprobe JSON output.

    Falls back to mutagen if ffprobe is unavailable.
    """
    # --- try ffprobe first ---
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                path,
            ],
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        )
        info = json.loads(result.stdout)
        return float(info["format"]["duration"])
    except (subprocess.CalledProcessError, FileNotFoundError, KeyError, ValueError):
        pass

    # --- fall back to mutagen ---
    try:
        from mutagen.mp3 import MP3

        audio = MP3(path)
        return float(audio.info.length)
    except Exception:
        pass

    # Last resort: estimate from file size (128 kbps ≈ 16 KB/s)
    try:
        import os

        size_bytes = os.path.getsize(path)
        return size_bytes / 16_000
    except Exception:
        return 0.0
