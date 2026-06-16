from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class TTSResult:
    """Result of a single TTS synthesis call.

    word_timestamps is a list of {"word": str, "start": float, "end": float}
    dicts (seconds). It may be empty when the provider/endpoint did not return
    character alignment (e.g. the plain text-to-speech fallback).
    """

    audio_path: str          # path to the written .mp3 file
    char_count: int          # billable characters submitted
    cost_usd: float          # real provider cost for this synthesis
    word_timestamps: list[dict] = field(default_factory=list)


class TTSService(ABC):
    """Abstract base for a text-to-speech provider."""

    provider: str

    @abstractmethod
    async def synthesize(
        self,
        text: str,
        voice_id: str,
        voice_settings: dict,
        out_path: str,
    ) -> TTSResult:
        """Synthesize ``text`` to an MP3 at ``out_path`` and return a TTSResult."""
        ...
