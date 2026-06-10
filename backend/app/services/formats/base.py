from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class FormatOutput:
    script: str
    hook_line: str
    estimated_duration_sec: int
    seo_title: str
    seo_description: str
    seo_tags: list[str]
    keywords: list[str]        # for image search
    voice_provider: str
    voice_id: str
    music_category: str
    cost_estimate_usd: float
    hashtags: list[str] = field(default_factory=list)
    thumbnail_text: str = ""


class FormatPlugin(ABC):
    slug: str
    name: str
    min_plan: str = "starter"

    @abstractmethod
    async def prepare(self, topic: str | None, channel_config: dict) -> FormatOutput:
        """Given a topic hint and channel config, return a complete FormatOutput.

        If topic is None, the plugin is responsible for discovering one
        (e.g. via Reddit trending posts).
        """
        ...

    @abstractmethod
    def estimate_cost(self, char_count: int) -> float:
        """Estimate the USD cost for this format given the TTS character count."""
        ...
