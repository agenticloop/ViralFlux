from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class TTSResult:
    audio_path: str      # path to .mp3 file
    duration_sec: float
    char_count: int


class TTSService(ABC):
    provider: str

    @abstractmethod
    async def synthesize(self, text: str, voice_id: str, output_path: str) -> TTSResult: ...

    @property
    @abstractmethod
    def cost_per_char(self) -> float: ...
