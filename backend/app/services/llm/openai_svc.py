from __future__ import annotations

import json
import logging

from openai import AsyncOpenAI

from app.core.config import settings
from .base import LLMService, ScriptResult, SEOResult, TopicResult

logger = logging.getLogger(__name__)


class LLMError(Exception):
    """Raised when an LLM API call fails or produces an unparseable response."""


class OpenAIService(LLMService):
    """OpenAI GPT-4o-mini implementation — used for analytical / SEO tasks."""

    def __init__(self) -> None:
        if not settings.OPENAI_API_KEY:
            raise LLMError("OPENAI_API_KEY is not set in configuration.")
        self._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self._model = settings.OPENAI_MODEL

    # ------------------------------------------------------------------
    # Script generation — delegate to Gemini
    # ------------------------------------------------------------------

    async def generate_script(self, raw_story: str, format_slug: str) -> ScriptResult:
        raise NotImplementedError("Use Gemini for script generation.")

    # ------------------------------------------------------------------
    # SEO generation
    # ------------------------------------------------------------------

    async def generate_seo(self, script: str, topic: str, format_slug: str) -> SEOResult:
        """Generate YouTube SEO metadata for a given script.

        Produces a title (≤70 chars), description (≤300 chars), 15 tags,
        5 hashtags, and punchy thumbnail text.
        """
        prompt = f"""You are a YouTube SEO expert specialising in horror Shorts.

Given the script and topic below, generate optimised YouTube metadata.

Topic: {topic}
Format: {format_slug}

Script:
{script}

Rules:
- title: max 70 characters, click-bait but not misleading, include a strong keyword
- description: max 300 characters, first sentence = hook, include 2–3 keywords naturally
- tags: exactly 15 tags (mix of broad and specific), each tag max 30 chars
- hashtags: exactly 5 hashtags (no # prefix in the list values, add # only in the value)
- thumbnail_text: ≤5 words, ALL CAPS, maximally shocking

Return ONLY valid JSON with these exact keys:
{{
  "title": "<YouTube title ≤70 chars>",
  "description": "<YouTube description ≤300 chars>",
  "tags": ["tag1", "tag2", ..., "tag15"],
  "hashtags": ["#hashtag1", "#hashtag2", "#hashtag3", "#hashtag4", "#hashtag5"],
  "thumbnail_text": "<≤5 word CAPS thumbnail text>"
}}"""

        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a YouTube SEO expert. Always respond with valid JSON only. "
                            "Never include markdown fences or explanatory text."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.6,
                max_tokens=600,
                response_format={"type": "json_object"},
            )
            raw_text = response.choices[0].message.content or ""
        except Exception as exc:
            logger.exception("OpenAI generate_seo failed")
            raise LLMError(f"OpenAI API error during SEO generation: {exc}") from exc

        try:
            data = json.loads(raw_text)
            title = data["title"][:70]
            description = data["description"][:300]
            tags: list[str] = data["tags"][:15]
            hashtags: list[str] = data["hashtags"][:5]

            # Ensure hashtags start with #
            hashtags = [h if h.startswith("#") else f"#{h}" for h in hashtags]

            return SEOResult(
                title=title,
                description=description,
                tags=tags,
                hashtags=hashtags,
                thumbnail_text=data.get("thumbnail_text", "")[:50],
            )
        except (json.JSONDecodeError, KeyError) as exc:
            logger.error("Failed to parse OpenAI SEO response: %s", raw_text)
            raise LLMError(
                f"Could not parse OpenAI SEO response as JSON: {exc}"
            ) from exc

    # ------------------------------------------------------------------
    # Topic picking
    # ------------------------------------------------------------------

    async def pick_topic(self, candidates: list[dict]) -> TopicResult:
        """Score candidates by virality and return the best TopicResult."""
        if not candidates:
            raise LLMError("No candidates provided to pick_topic.")

        candidates_json = json.dumps(
            [
                {
                    "index": i,
                    "title": c.get("title", ""),
                    "score": c.get("score", 0),
                    "url": c.get("url", ""),
                    "snippet": (c.get("text") or "")[:300],
                }
                for i, c in enumerate(candidates)
            ],
            indent=2,
        )

        prompt = f"""Analyse these Reddit posts for YouTube Shorts virality potential.
Pick the single best story for a 60-second horror Short.

Candidates:
{candidates_json}

Score each on: visual imagery, universal fear, clear narrative arc, title hook potential.

Return ONLY valid JSON:
{{
  "recommended_topic": "<title of the best post>",
  "source_url": "<url of the best post>",
  "confidence_score": <float 0.0-1.0>,
  "reasoning": "<2-3 sentence explanation>",
  "alternative_topics": ["<second best title>", "<third best title>"]
}}"""

        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a YouTube virality analyst. "
                            "Always respond with valid JSON only."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=512,
                response_format={"type": "json_object"},
            )
            raw_text = response.choices[0].message.content or ""
        except Exception as exc:
            logger.exception("OpenAI pick_topic failed")
            raise LLMError(f"OpenAI API error during topic picking: {exc}") from exc

        try:
            data = json.loads(raw_text)
            return TopicResult(
                recommended_topic=data["recommended_topic"],
                source_url=data["source_url"],
                confidence_score=float(data["confidence_score"]),
                reasoning=data["reasoning"],
                alternative_topics=data.get("alternative_topics", []),
            )
        except (json.JSONDecodeError, KeyError) as exc:
            logger.error("Failed to parse OpenAI pick_topic response: %s", raw_text)
            raise LLMError(
                f"Could not parse OpenAI pick_topic response as JSON: {exc}"
            ) from exc


def get_openai() -> OpenAIService:
    """Dependency-injection factory for OpenAIService."""
    return OpenAIService()
