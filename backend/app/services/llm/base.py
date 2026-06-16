from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ScriptResult:
    """Result of a script generation call.

    ``scenes`` is a list of scene dicts, each shaped as::

        {"text": str, "image_prompt": str, "start_hint": float | None}

    ``image_prompts`` is a convenience flat list of the per-scene image prompts
    (same order as ``scenes``). For loop-footage genres (e.g. brainrot) the
    image prompts may be empty strings.
    """

    script: str
    scenes: list[dict] = field(default_factory=list)
    image_prompts: list[str] = field(default_factory=list)


@dataclass
class SEOResult:
    """YouTube Shorts SEO metadata."""

    title: str            # <= 100 chars
    description: str
    tags: list[str] = field(default_factory=list)  # 5-15 tags


class LLMService(ABC):
    """Abstract base for the ViralFlux LLM layer (Gemini-only, 3 tiers)."""

    @abstractmethod
    async def generate_script(
        self,
        genre: str,
        seed: str | None,
        duration_tier: str,
        model_tier: str,
        char_limit: int,
    ) -> ScriptResult: ...

    @abstractmethod
    async def generate_seo(
        self,
        genre: str,
        script: str,
        model_tier: str,
    ) -> SEOResult: ...

    @abstractmethod
    async def generate_seed_ideas(
        self,
        genre: str,
        weekly_seed: str,
        count: int,
        model_tier: str,
    ) -> list[str]: ...
