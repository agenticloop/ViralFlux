from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ScriptResult:
    script_text: str
    estimated_duration_sec: int
    hook_line: str


@dataclass
class SEOResult:
    title: str           # max 70 chars
    description: str     # max 300 chars
    tags: list[str]      # 15 tags
    hashtags: list[str]  # 5 hashtags
    thumbnail_text: str


@dataclass
class TopicResult:
    recommended_topic: str
    source_url: str
    confidence_score: float
    reasoning: str
    alternative_topics: list[str]


class LLMService(ABC):
    @abstractmethod
    async def generate_script(self, raw_story: str, format_slug: str) -> ScriptResult: ...

    @abstractmethod
    async def generate_seo(self, script: str, topic: str, format_slug: str) -> SEOResult: ...

    @abstractmethod
    async def pick_topic(self, candidates: list[dict]) -> TopicResult: ...
