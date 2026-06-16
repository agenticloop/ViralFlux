"""TTS layer — ElevenLabs only.

edge-tts and google-tts have been removed; ElevenLabs is the sole provider.
"""
from __future__ import annotations

from .base import TTSResult, TTSService
from .elevenlabs import ElevenLabsError, ElevenLabsService, elevenlabs_service
from .voice_catalog import recommended_voices, voice_catalog

__all__ = [
    "TTSResult",
    "TTSService",
    "ElevenLabsService",
    "ElevenLabsError",
    "elevenlabs_service",
    "voice_catalog",
    "recommended_voices",
]
