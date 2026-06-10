from __future__ import annotations

import json
import logging
import subprocess

from app.core.config import settings
from .base import TTSService, TTSResult

logger = logging.getLogger(__name__)

_DEFAULT_VOICE = "en-US-Neural2-D"
_DEFAULT_LANGUAGE = "en-US"


class TTSError(Exception):
    """Raised when a TTS synthesis operation fails."""


class GoogleTTSService(TTSService):
    """Google Cloud Text-to-Speech service."""

    provider = "google-tts"

    @property
    def cost_per_char(self) -> float:
        return 0.000004  # $4 per 1M characters (Neural2 tier)

    def __init__(self) -> None:
        if not settings.GOOGLE_TTS_API_KEY:
            raise TTSError(
                "GOOGLE_TTS_API_KEY is not set. "
                "Set it in your .env file or environment variables."
            )
        self._api_key = settings.GOOGLE_TTS_API_KEY

    async def synthesize(self, text: str, voice_id: str, output_path: str) -> TTSResult:
        """Synthesise text using Google Cloud TTS and save MP3 to output_path."""
        if not text.strip():
            raise TTSError("Cannot synthesise empty text.")

        voice_name = voice_id or _DEFAULT_VOICE

        try:
            from google.cloud import texttospeech_v1 as tts

            # Build client with API key credential
            client = tts.TextToSpeechClient(
                client_options={"api_key": self._api_key}
            )

            synthesis_input = tts.SynthesisInput(text=text)

            voice_params = tts.VoiceSelectionParams(
                language_code=_DEFAULT_LANGUAGE,
                name=voice_name,
            )

            audio_config = tts.AudioConfig(
                audio_encoding=tts.AudioEncoding.MP3,
                speaking_rate=1.0,
                pitch=0.0,
            )

            response = client.synthesize_speech(
                input=synthesis_input,
                voice=voice_params,
                audio_config=audio_config,
            )

            with open(output_path, "wb") as f:
                f.write(response.audio_content)

        except TTSError:
            raise
        except Exception as exc:
            logger.exception("Google TTS synthesis failed for voice %s", voice_name)
            raise TTSError(f"Google Cloud TTS API error: {exc}") from exc

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
