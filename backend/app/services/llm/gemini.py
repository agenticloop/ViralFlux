from __future__ import annotations

import asyncio
import json
import logging
import math
import re
from typing import Any

import google.generativeai as genai

from app.core.config import settings
from app.core.genres import VISUAL_LOOP, get_genre
from app.core.pricing import DURATION_CHARS, DURATION_SECONDS

from .base import LLMService, ScriptResult, SEOResult

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Tuning knobs
# --------------------------------------------------------------------------- #
_MAX_RETRIES = 3
_RETRY_BASE_DELAY = 1.0          # seconds; exponential backoff base
_REQUEST_TIMEOUT = 60.0          # seconds per attempt
_SECONDS_PER_SCENE = 5.0         # ~1 scene per 4-6s of narration
_MIN_SCENES = 2
_MAX_SCENES = 40
# Rough chars/token ratio (~4) used to size the output token budget generously.
_CHARS_PER_TOKEN = 4


class LLMError(RuntimeError):
    """Raised when an LLM call fails or the layer is misconfigured."""


def _strip_code_fences(text: str) -> str:
    """Remove markdown ```json ... ``` or ``` ... ``` fences from a string."""
    text = (text or "").strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _scene_count_for(duration_tier: str) -> int:
    seconds = DURATION_SECONDS.get(duration_tier, 60)
    n = round(seconds / _SECONDS_PER_SCENE)
    return max(_MIN_SCENES, min(_MAX_SCENES, int(n)))


def _target_chars(duration_tier: str, char_limit: int) -> int:
    """Target narration length: duration target, capped by the plan char limit."""
    target = DURATION_CHARS.get(duration_tier, 900)
    return min(target, max(1, char_limit))


def _trim_to_budget(script: str, char_limit: int) -> str:
    """Trim a script to at most ``char_limit`` chars without cutting mid-word.

    Prefers to break on sentence boundaries, then word boundaries.
    """
    script = (script or "").strip()
    if len(script) <= char_limit:
        return script

    window = script[:char_limit]
    # Prefer the last sentence-ending punctuation in the window.
    sentence_end = max(window.rfind(". "), window.rfind("! "), window.rfind("? "))
    if sentence_end >= int(char_limit * 0.6):
        return window[: sentence_end + 1].strip()

    # Otherwise break on the last whitespace.
    space = window.rfind(" ")
    if space >= int(char_limit * 0.5):
        return window[:space].strip()

    return window.strip()


class GeminiService(LLMService):
    """Gemini-only LLM service for ViralFlux (3 UI tiers: Lite/Balanced/Max).

    Models are resolved per-call from ``settings.gemini_model_for_tier`` so a
    single service instance serves every tier. The SDK is configured lazily and
    only once; with an empty ``GOOGLE_AI_API_KEY`` every call raises a clear
    :class:`LLMError` instead of failing deep inside the SDK.
    """

    def __init__(self) -> None:
        self._configured = False
        self._models: dict[str, genai.GenerativeModel] = {}
        self._configure_lock = asyncio.Lock()

    # ------------------------------------------------------------------ #
    # Configuration / model resolution
    # ------------------------------------------------------------------ #
    def _ensure_configured(self) -> None:
        if self._configured:
            return
        if not settings.GOOGLE_AI_API_KEY:
            raise LLMError(
                "GOOGLE_AI_API_KEY is not set — the Gemini LLM layer is disabled. "
                "Set a real Google AI Studio API key to enable script/SEO generation."
            )
        genai.configure(api_key=settings.GOOGLE_AI_API_KEY)
        self._configured = True

    def _model_for(self, model_tier: str) -> genai.GenerativeModel:
        """Resolve and cache a GenerativeModel for a UI tier."""
        self._ensure_configured()
        model_id = settings.gemini_model_for_tier(model_tier)
        model = self._models.get(model_id)
        if model is None:
            model = genai.GenerativeModel(model_id)
            self._models[model_id] = model
        return model

    # ------------------------------------------------------------------ #
    # Core JSON call with retry + timeout
    # ------------------------------------------------------------------ #
    async def _generate_json(
        self,
        model_tier: str,
        prompt: str,
        *,
        temperature: float,
        max_output_tokens: int,
    ) -> Any:
        """Run a Gemini call in JSON mode and return the parsed object.

        Retries transient failures with exponential backoff and enforces a
        per-attempt timeout.
        """
        model = self._model_for(model_tier)
        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            response_mime_type="application/json",
        )

        last_exc: Exception | None = None
        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                response = await asyncio.wait_for(
                    model.generate_content_async(
                        prompt, generation_config=generation_config
                    ),
                    timeout=_REQUEST_TIMEOUT,
                )
                raw_text = getattr(response, "text", None)
                if not raw_text:
                    raise LLMError("Gemini returned an empty response.")
                return json.loads(_strip_code_fences(raw_text))
            except json.JSONDecodeError as exc:
                # A malformed JSON body is worth one more shot, but log it.
                last_exc = exc
                logger.warning(
                    "Gemini JSON parse failed (attempt %d/%d): %s",
                    attempt,
                    _MAX_RETRIES,
                    exc,
                )
            except asyncio.TimeoutError as exc:
                last_exc = exc
                logger.warning(
                    "Gemini call timed out after %.0fs (attempt %d/%d)",
                    _REQUEST_TIMEOUT,
                    attempt,
                    _MAX_RETRIES,
                )
            except LLMError:
                raise
            except Exception as exc:  # SDK/network/quota errors
                last_exc = exc
                logger.warning(
                    "Gemini call failed (attempt %d/%d): %s",
                    attempt,
                    _MAX_RETRIES,
                    exc,
                )

            if attempt < _MAX_RETRIES:
                await asyncio.sleep(_RETRY_BASE_DELAY * (2 ** (attempt - 1)))

        raise LLMError(
            f"Gemini call failed after {_MAX_RETRIES} attempts: {last_exc}"
        ) from last_exc

    # ------------------------------------------------------------------ #
    # 1. Script generation
    # ------------------------------------------------------------------ #
    async def generate_script(
        self,
        genre: str,
        seed: str | None,
        duration_tier: str,
        model_tier: str,
        char_limit: int,
    ) -> ScriptResult:
        """Generate a narration script + scene breakdown for a short.

        Targets ``DURATION_CHARS[duration_tier]`` characters but never exceeds
        ``char_limit``. Produces ~1 scene per 4-6s of narration. Each scene gets
        an image prompt prefixed with the genre's ``image_style_prefix``. For
        loop-footage genres (brainrot) image prompts are returned empty.
        """
        g = get_genre(genre)
        is_loop = g.get("visual") == VISUAL_LOOP
        style_prefix = (g.get("image_style_prefix") or "").strip()

        target = _target_chars(duration_tier, char_limit)
        n_scenes = _scene_count_for(duration_tier)
        seconds = DURATION_SECONDS.get(duration_tier, 60)
        seed_text = (seed or "").strip()

        visual_instruction = (
            "This genre plays over looping background footage, so DO NOT write "
            "image prompts — set every \"image_prompt\" to an empty string \"\"."
            if is_loop
            else (
                "For each scene write a vivid, concrete English image_prompt "
                "(subject + setting + lighting + mood). Do NOT repeat the style "
                "prefix — it is added automatically. Keep each under 40 words."
            )
        )

        seed_block = (
            f"Seed idea / topic to base the script on:\n{seed_text}\n\n"
            if seed_text
            else "No seed was given — invent a fresh, original concept that fits the genre.\n\n"
        )

        prompt = f"""You are an expert scriptwriter for vertical (9:16) YouTube Shorts.

Genre: {g.get("name", genre)}
Genre style: {g.get("description", "")}

{seed_block}Write the narration as ONE continuous spoken script (no scene labels,
no stage directions inside the script text — just what the narrator says).

HARD CONSTRAINTS:
- Total narration length: about {target} characters, and ABSOLUTELY NO MORE than {char_limit} characters.
- It must read naturally in about {seconds} seconds at a normal narration pace.
- Open with a 1-sentence hook in the first ~2 seconds.
- Punchy, no filler. Every sentence earns its place.

Then split that SAME narration into exactly {n_scenes} ordered scenes that
together reproduce the full script with no gaps and no overlaps. Each scene
covers a contiguous slice of the narration.

{visual_instruction}

For "start_hint", give the approximate start time of each scene in seconds
(a float from 0.0 up to about {seconds}.0), evenly progressing.

Return ONLY valid JSON with this exact shape:
{{
  "script": "<the full narration, the concatenation of all scene texts>",
  "scenes": [
    {{"text": "<narration for this scene>", "image_prompt": "<image prompt or empty>", "start_hint": <float>}}
  ]
}}"""

        max_tokens = min(8192, max(512, int((char_limit * 2) / _CHARS_PER_TOKEN) + 512))
        data = await self._generate_json(
            model_tier,
            prompt,
            temperature=0.9,
            max_output_tokens=max_tokens,
        )

        return self._build_script_result(
            data,
            char_limit=char_limit,
            seconds=seconds,
            style_prefix="" if is_loop else style_prefix,
            is_loop=is_loop,
        )

    def _build_script_result(
        self,
        data: Any,
        *,
        char_limit: int,
        seconds: int,
        style_prefix: str,
        is_loop: bool,
    ) -> ScriptResult:
        if not isinstance(data, dict):
            raise LLMError("Gemini script response was not a JSON object.")

        raw_scenes = data.get("scenes") or []
        if not isinstance(raw_scenes, list):
            raw_scenes = []

        scenes: list[dict] = []
        for i, raw in enumerate(raw_scenes):
            if not isinstance(raw, dict):
                continue
            text = str(raw.get("text", "")).strip()
            if not text:
                continue

            img = str(raw.get("image_prompt", "") or "").strip()
            if is_loop:
                img = ""
            elif img and style_prefix and style_prefix.lower() not in img.lower():
                img = f"{style_prefix}, {img}"

            start_hint = raw.get("start_hint")
            try:
                start_hint = float(start_hint) if start_hint is not None else None
            except (TypeError, ValueError):
                start_hint = None

            scenes.append(
                {"text": text, "image_prompt": img, "start_hint": start_hint}
            )

        # Prefer the model's full script; fall back to joining scene texts.
        script = str(data.get("script", "") or "").strip()
        if not script and scenes:
            script = " ".join(s["text"] for s in scenes)
        if not script:
            raise LLMError("Gemini returned an empty script.")

        # Enforce the hard char budget on the narration.
        script = _trim_to_budget(script, char_limit)

        # Backfill start hints if missing / non-monotonic.
        if scenes:
            self._normalize_start_hints(scenes, seconds)

        image_prompts = [s["image_prompt"] for s in scenes]
        return ScriptResult(script=script, scenes=scenes, image_prompts=image_prompts)

    @staticmethod
    def _normalize_start_hints(scenes: list[dict], seconds: int) -> None:
        n = len(scenes)
        needs_fill = any(s.get("start_hint") is None for s in scenes)
        # Detect non-monotonic ordering.
        prev = -1.0
        monotonic = True
        for s in scenes:
            h = s.get("start_hint")
            if h is None or h < prev:
                monotonic = False
                break
            prev = float(h)
        if needs_fill or not monotonic:
            step = seconds / n if n else 0.0
            for i, s in enumerate(scenes):
                s["start_hint"] = round(i * step, 2)

    # ------------------------------------------------------------------ #
    # 2. SEO generation (replaces the deleted OpenAI SEO)
    # ------------------------------------------------------------------ #
    async def generate_seo(
        self,
        genre: str,
        script: str,
        model_tier: str,
    ) -> SEOResult:
        """Generate YouTube Shorts SEO metadata from a narration script."""
        g = get_genre(genre)
        snippet = (script or "").strip()[:2000]
        if not snippet:
            raise LLMError("Cannot generate SEO for an empty script.")

        prompt = f"""You are a YouTube Shorts SEO expert for {g.get("name", genre)} content.

Genre style: {g.get("description", "")}

Here is the narration script of a vertical short:
---
{snippet}
---

Produce optimized YouTube metadata that maximises click-through and discovery.

RULES:
- title: <= 100 characters, punchy, curiosity-driven, no clickbait emojis spam (one emoji max).
- description: 1-3 sentences (<= 400 chars), then 3-5 relevant hashtags on a new line.
- tags: between 5 and 15 lowercase keyword tags, no '#', single or short multi-word phrases.

Return ONLY valid JSON with this exact shape:
{{
  "title": "<= 100 char title",
  "description": "<short description with #hashtags>",
  "tags": ["tag one", "tag two", "..."]
}}"""

        data = await self._generate_json(
            model_tier,
            prompt,
            temperature=0.7,
            max_output_tokens=1024,
        )
        if not isinstance(data, dict):
            raise LLMError("Gemini SEO response was not a JSON object.")

        title = str(data.get("title", "") or "").strip()[:100]
        description = str(data.get("description", "") or "").strip()

        raw_tags = data.get("tags") or []
        tags: list[str] = []
        if isinstance(raw_tags, list):
            for t in raw_tags:
                t = str(t).strip().lstrip("#").strip()
                if t and t.lower() not in {x.lower() for x in tags}:
                    tags.append(t)
        tags = tags[:15]

        if not title:
            raise LLMError("Gemini SEO response had no title.")

        return SEOResult(title=title, description=description, tags=tags)

    # ------------------------------------------------------------------ #
    # 3. Seed idea expansion (used by the scheduler)
    # ------------------------------------------------------------------ #
    async def generate_seed_ideas(
        self,
        genre: str,
        weekly_seed: str,
        count: int,
        model_tier: str,
    ) -> list[str]:
        """Expand a channel's weekly seed prompt into ``count`` concrete ideas."""
        count = max(1, min(50, int(count)))
        g = get_genre(genre)
        seed = (weekly_seed or "").strip()

        seed_block = (
            f"The channel's weekly seed prompt is:\n\"{seed}\"\n\n"
            if seed
            else "The channel gave no specific seed — generate strong on-genre ideas.\n\n"
        )

        prompt = f"""You are a content strategist for a {g.get("name", genre)} YouTube Shorts channel.

Genre style: {g.get("description", "")}

{seed_block}Generate exactly {count} DISTINCT, concrete video ideas. Each idea must be a
single specific concept (not a category) that can be turned directly into a
short narration script. Keep each idea to one sentence, vivid and self-contained.

Return ONLY valid JSON with this exact shape:
{{"ideas": ["idea 1", "idea 2", "..."]}}"""

        data = await self._generate_json(
            model_tier,
            prompt,
            temperature=1.0,
            max_output_tokens=2048,
        )

        raw_ideas: Any
        if isinstance(data, dict):
            raw_ideas = data.get("ideas") or []
        elif isinstance(data, list):
            raw_ideas = data
        else:
            raw_ideas = []

        ideas: list[str] = []
        for item in raw_ideas:
            text = str(item).strip()
            if text and text.lower() not in {x.lower() for x in ideas}:
                ideas.append(text)

        if not ideas:
            raise LLMError("Gemini returned no seed ideas.")

        return ideas[:count]


# --------------------------------------------------------------------------- #
# Module-level singleton
# --------------------------------------------------------------------------- #
# Constructing the service is cheap and does NOT touch the network or require a
# key — configuration happens lazily on first call. This makes import-time safe
# even with an empty GOOGLE_AI_API_KEY.
gemini_service = GeminiService()


def get_gemini() -> GeminiService:
    """Dependency-injection accessor for the shared GeminiService singleton."""
    return gemini_service
