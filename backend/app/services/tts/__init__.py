from .base import TTSService, TTSResult
from .edge_tts import EdgeTTSService
from .elevenlabs import ElevenLabsService
from .google_tts import GoogleTTSService


def get_tts_service(provider: str) -> TTSService:
    """Factory: return the TTS service for the given provider string.

    Defaults to EdgeTTSService (free, no API key required).
    """
    match provider:
        case "edge-tts":
            return EdgeTTSService()
        case "elevenlabs":
            return ElevenLabsService()
        case "google-tts":
            return GoogleTTSService()
        case _:
            return EdgeTTSService()  # safe free default


__all__ = [
    "TTSService",
    "TTSResult",
    "EdgeTTSService",
    "ElevenLabsService",
    "GoogleTTSService",
    "get_tts_service",
]
