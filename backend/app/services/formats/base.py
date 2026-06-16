from __future__ import annotations

import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.core import genres as genres_mod
from app.core import pricing

logger = logging.getLogger(__name__)


@dataclass
class FormatOutput:
    """Everything the video pipeline needs to render one video.

    Produced by a FormatPlugin.prepare() from a VideoJob + channel. The pipeline
    consumes this verbatim — it never re-reads the job for generation params.
    """

    script: str
    scenes: list[dict]
    image_prompts: list[str]
    seo_title: str
    seo_description: str
    seo_tags: list[str]
    voice_id: str
    voice_settings: dict
    visual: str            # "generated_images" | "loop_footage"
    music_bucket: str
    caption_style: str     # "horror" | "brainrot"


class FormatPlugin(ABC):
    """A genre-driven content format. format == genre.

    Subclasses set ``genre`` and may override ``prepare``; the default
    implementation in this base handles all three current genres.
    """

    genre: str

    @abstractmethod
    async def prepare(self, job, channel) -> FormatOutput:  # pragma: no cover
        ...

    # ------------------------------------------------------------------
    # Shared preparation logic (used by all built-in plugins)
    # ------------------------------------------------------------------

    async def _prepare(self, job, channel) -> FormatOutput:
        """Resolve script, scenes, image prompts, SEO and voice config.

        - manual script_source: use ``job.script`` verbatim; derive scenes by
          chunking and prefix the genre image style to each chunk gist.
        - seed/ai: call gemini_service.generate_script with the job topic.
        Always generates SEO. Degrades gracefully if upstream LLM/keys missing.
        """
        from app.services.llm import gemini_service

        cfg = genres_mod.get_genre(job.genre)
        duration_tier = getattr(job, "duration_tier", None) or "30s"
        model_tier = getattr(job, "model_tier", None) or "Lite"
        char_limit = pricing.DURATION_CHARS.get(duration_tier, 450)

        script_source = getattr(job, "script_source", "ai") or "ai"
        manual_script = (getattr(job, "script", None) or "").strip()

        if script_source == "manual" and manual_script:
            script = manual_script
            scenes, image_prompts = self._scene_break(script, cfg, duration_tier)
        else:
            seed = getattr(job, "topic", None)
            result = await gemini_service.generate_script(
                genre=job.genre,
                seed=seed,
                duration_tier=duration_tier,
                model_tier=model_tier,
                char_limit=char_limit,
            )
            script = result.script
            scenes = list(result.scenes or [])
            image_prompts = list(result.image_prompts or [])
            # Backfill scenes/prompts for generated-image genres if the model
            # returned none.
            if cfg["visual"] == genres_mod.VISUAL_GENERATED and not image_prompts:
                scenes, image_prompts = self._scene_break(script, cfg, duration_tier)

        seo_title, seo_description, seo_tags = await self._safe_seo(
            gemini_service, job.genre, script, model_tier
        )

        voice_id = (
            getattr(job, "voice_id", None)
            or getattr(channel, "voice_id", None)
            or cfg["default_voice_id"]
        )
        voice_settings = (
            getattr(job, "voice_settings", None)
            or getattr(channel, "voice_settings", None)
            or cfg["voice_settings"]
        )

        return FormatOutput(
            script=script,
            scenes=scenes,
            image_prompts=image_prompts,
            seo_title=seo_title,
            seo_description=seo_description,
            seo_tags=seo_tags,
            voice_id=voice_id,
            voice_settings=dict(voice_settings),
            visual=cfg["visual"],
            music_bucket=cfg["music_bucket"],
            caption_style=cfg["caption_style"],
        )

    async def _safe_seo(self, gemini_service, genre, script, model_tier):
        try:
            seo = await gemini_service.generate_seo(
                genre=genre, script=script, model_tier=model_tier
            )
            return seo.title, seo.description, list(seo.tags or [])
        except Exception as exc:  # degrade gracefully
            logger.warning("SEO generation failed for genre=%s: %s", genre, exc)
            fallback = (script.strip().split("\n", 1)[0] or genre.title())[:100]
            return fallback, script[:200], [genre]

    def _scene_break(
        self, script: str, cfg: dict, duration_tier: str
    ) -> tuple[list[dict], list[str]]:
        """Chunk a script into ~(duration/5) scenes and synthesize image prompts.

        Used for manual scripts and as a fallback for generated-image genres
        when the model returns no prompts.
        """
        total_sec = pricing.DURATION_SECONDS.get(duration_tier, 30)
        n_scenes = max(1, total_sec // 5)
        prefix = cfg.get("image_style_prefix", "").strip()

        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", script) if s.strip()]
        if not sentences:
            sentences = [script.strip()] if script.strip() else [cfg["name"]]

        per = max(1, len(sentences) // n_scenes)
        chunks: list[str] = []
        for i in range(0, len(sentences), per):
            chunks.append(" ".join(sentences[i : i + per]))
        chunks = chunks[:n_scenes] or [script.strip()]

        seg = (total_sec / len(chunks)) if chunks else float(total_sec)
        scenes: list[dict] = []
        image_prompts: list[str] = []
        for idx, chunk in enumerate(chunks):
            gist = chunk[:160]
            prompt = f"{prefix}, {gist}".strip(", ") if prefix else gist
            scenes.append(
                {
                    "text": chunk,
                    "image_prompt": prompt,
                    "start_hint": round(idx * seg, 2),
                }
            )
            image_prompts.append(prompt)
        return scenes, image_prompts
