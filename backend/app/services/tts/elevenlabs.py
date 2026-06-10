from __future__ import annotations

import json
import logging
import subprocess

from app.core.config import settings
from .base import TTSService, TTSResult

logger = logging.getLogger(__name__)

_MODEL_ID = "eleven_monolingual_v1"
_DEFAULT_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # "Rachel" — neutral narrator voice


class TTSError(Exception):
    """Raised when a TTS synthesis operation fails."""


class ElevenLabsService(TTSService):
    """ElevenLabs API TTS service."""

    provider = "elevenlabs"

    @property
    def cost_per_char(self) -> float:
        return 0.00018  # approximate cost per character

    def __init__(self) -> None:
        if not settings.ELEVENLABS_API_KEY:
            raise TTSError(
                "ELEVENLABS_API_KEY is not set. "
                "Set it in your .env file or environment variables."
            )
        self._api_key = settings.ELEVENLABS_API_KEY

    async def synthesize(self, text: str, voice_id: str, output_path: str) -> TTSResult:
        """Synthesise text using ElevenLabs and save MP3 to output_path."""
        if not text.strip():
            raise TTSError("Cannot synthesise empty text.")

        vid = voice_id or _DEFAULT_VOICE_ID

        try:
            from elevenlabs import generate, set_api_key, save

            set_api_key(self._api_key)
            audio_bytes = generate(
                text=text,
                voice=vid,
                model=_MODEL_ID,
            )
            save(audio_bytes, output_path)
        except TTSError:
            raise
        except Exception as exc:
            logger.exception("ElevenLabs synthesis failed for voice %s", vid)
            raise TTSError(f"ElevenLabs API error: {exc}") from exc

        duration = _get_duration_ffprobe(output_path)
        return TTSResult(
            audio_path=output_path,
            duration_sec=duration,
            char_count=len(text),
        )


def _get_duration_ffprobe(path: str) -> float:
    """Return audio duration in seconds via ffprobe, with mutagen fallback."""
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

    try:
        from mutagen.mp3 import MP3

        audio = MP3(path)
        return float(audio.info.length)
    except Exception:
        return 0.0
