from __future__ import annotations

import json
import logging
import re

import google.generativeai as genai

from app.core.config import settings
from .base import LLMService, ScriptResult, SEOResult, TopicResult

logger = logging.getLogger(__name__)


class LLMError(Exception):
    """Raised when an LLM call fails."""


def _strip_code_fences(text: str) -> str:
    """Remove markdown ```json ... ``` or ``` ... ``` fences from a string."""
    text = text.strip()
    # Remove leading ```json or ``` fence
    text = re.sub(r"^```(?:json)?\s*", "", text)
    # Remove trailing ``` fence
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


class GeminiService(LLMService):
    """Google Gemini Flash implementation — used for creative tasks (script generation)."""

    def __init__(self) -> None:
        if not settings.GOOGLE_AI_API_KEY:
            raise LLMError("GOOGLE_AI_API_KEY is not set in configuration.")
        genai.configure(api_key=settings.GOOGLE_AI_API_KEY)
        self._model = genai.GenerativeModel(settings.GEMINI_MODEL)

    # ------------------------------------------------------------------
    # Script generation
    # ------------------------------------------------------------------

    async def generate_script(self, raw_story: str, format_slug: str) -> ScriptResult:
        """Generate a narrated horror-short script from a raw story/topic.

        Returns a ScriptResult with parsed fields.
        """
        system_prompt = (
            "You are a master horror story narrator for YouTube Shorts. "
            "Your style: visceral, punchy sentences, short paragraphs. "
            "You hook viewers in the first 2 seconds and deliver a gut-punch at 15 seconds. "
            "You NEVER use filler words. Every word earns its place."
        )

        user_prompt = f"""Write a YouTube Shorts horror narration script (max 160 words) based on the following story/topic.

Topic / Story:
{raw_story}

Rules:
1. Hook line in the first sentence (extremely gripping, ≤15 words).
2. Build dread fast — punchy sentences, no filler.
3. Second hook at ~15 seconds (roughly word 35–45).
4. End with a disturbing final line.
5. Target reading time: 45–58 seconds at normal narration pace.

Return ONLY valid JSON with these exact keys:
{{
  "script_text": "<full narration script>",
  "hook_line": "<the opening hook sentence only>",
  "estimated_duration_sec": <integer between 45 and 58>
}}"""

        try:
            response = await self._model.generate_content_async(
                f"{system_prompt}\n\n{user_prompt}",
                generation_config=genai.types.GenerationConfig(
                    temperature=0.85,
                    max_output_tokens=512,
                ),
            )
            raw_text = response.text
        except Exception as exc:
            logger.exception("Gemini generate_script failed")
            raise LLMError(f"Gemini API error during script generation: {exc}") from exc

        try:
            cleaned = _strip_code_fences(raw_text)
            data = json.loads(cleaned)
            return ScriptResult(
                script_text=data["script_text"],
                estimated_duration_sec=int(data["estimated_duration_sec"]),
                hook_line=data["hook_line"],
            )
        except (json.JSONDecodeError, KeyError) as exc:
            logger.error("Failed to parse Gemini script response: %s", raw_text)
            raise LLMError(
                f"Could not parse Gemini script response as JSON: {exc}"
            ) from exc

    # ------------------------------------------------------------------
    # SEO generation — delegate to OpenAI
    # ------------------------------------------------------------------

    async def generate_seo(self, script: str, topic: str, format_slug: str) -> SEOResult:
        raise NotImplementedError("Use OpenAI for SEO")

    # ------------------------------------------------------------------
    # Topic picking
    # ------------------------------------------------------------------

    async def pick_topic(self, candidates: list[dict]) -> TopicResult:
        """Analyse a list of candidate story posts and pick the most viral one.

        Each candidate dict should have keys: title, score, url, text (optional).
        """
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

        prompt = f"""You are a YouTube Shorts virality analyst specialising in horror content.

Below are Reddit posts from horror subreddits. Pick the ONE story most likely to go viral as a 60-second horror Short.

Candidates (JSON):
{candidates_json}

Criteria for virality:
- Strong visual imagery
- Universal fear (not niche)
- Clear narrative arc completable in 60 s
- Provocative title / hook potential

Return ONLY valid JSON with these exact keys:
{{
  "recommended_topic": "<title of the best post>",
  "source_url": "<url of the best post>",
  "confidence_score": <float 0.0–1.0>,
  "reasoning": "<2-3 sentence explanation>",
  "alternative_topics": ["<second best title>", "<third best title>"]
}}"""

        try:
            response = await self._model.generate_content_async(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.4,
                    max_output_tokens=512,
                ),
            )
            raw_text = response.text
        except Exception as exc:
            logger.exception("Gemini pick_topic failed")
            raise LLMError(f"Gemini API error during topic picking: {exc}") from exc

        try:
            cleaned = _strip_code_fences(raw_text)
            data = json.loads(cleaned)
            return TopicResult(
                recommended_topic=data["recommended_topic"],
                source_url=data["source_url"],
                confidence_score=float(data["confidence_score"]),
                reasoning=data["reasoning"],
                alternative_topics=data.get("alternative_topics", []),
            )
        except (json.JSONDecodeError, KeyError) as exc:
            logger.error("Failed to parse Gemini pick_topic response: %s", raw_text)
            raise LLMError(
                f"Could not parse Gemini pick_topic response as JSON: {exc}"
            ) from exc


def get_gemini() -> GeminiService:
    """Dependency-injection factory for GeminiService."""
    return GeminiService()
