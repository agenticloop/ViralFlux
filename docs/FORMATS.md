# ViralFlux — Genres & Genre Handlers

ViralFlux organizes content into **genres**. In v2 the three genres are **Horror**, **Brainrot**, and **Custom** (Pro/Agency). Each genre is implemented as a self-contained handler that knows how to generate a script + SEO (Gemini), pick its visual path (Imagen images for Horror, CC0 footage for Brainrot), configure audio (ElevenLabs voice + CC0 music), and report the credit cost. The core video pipeline is genre-agnostic; it delegates all content decisions to the active genre handler.

> **v2 note:** the old open-ended "format plugin" list (ranking, motivational, clip-stitch, news, etc.) is gone, as are its dependencies: OpenAI for SEO, Pexels/Pixabay/Unsplash for images, edge-tts/Google TTS for voice, and Reddit/subreddit scraping for topics. Everything below reflects the current single-LLM (Gemini), single-TTS (ElevenLabs), Imagen-or-footage stack. The base class still lives at `backend/app/services/formats/base.py`; only the providers and the genre set changed.

---

## FormatPlugin Interface

Every format must extend the `FormatPlugin` abstract base class located at:

```
backend/app/services/formats/base.py
```

### Required Methods and Properties

```python
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal


@dataclass
class FormatOutput:
    """Result returned by FormatPlugin.prepare()."""
    script: str                    # Full narration script text
    seo_title: str                 # YouTube title (max 70 chars)
    seo_description: str           # YouTube description (max 300 chars)
    seo_tags: list[str]            # 15 SEO tags
    voice_id: str                  # ElevenLabs voice ID (only provider)
    music_category: str            # Music folder slug (e.g., "horror_ambient")
    pipeline_steps: list[str]      # Steps the video pipeline should run
    credit_cost: int               # Credits debited for this job (see pricing.py)


class FormatPlugin(ABC):

    @property
    @abstractmethod
    def slug(self) -> str:
        """Unique identifier for this format (e.g., 'horror_story').
        
        Must match the value stored in video_jobs.format_slug and the
        content_formats.slug database row.
        """
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable display name (e.g., 'Horror Story Shorts')."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """One-sentence description shown in the dashboard format picker."""
        ...

    @property
    @abstractmethod
    def min_plan(self) -> str:
        """Minimum plan slug required to use this genre.

        One of: 'free', 'starter', 'pro', 'agency'.
        (Custom genres are gated to 'pro' and above.)
        """
        ...

    @property
    @abstractmethod
    def default_music_category(self) -> str:
        """Default music category slug for this format.
        
        Must correspond to a directory under /assets/music/.
        """
        ...

    @abstractmethod
    async def prepare(
        self,
        topic: str | None,
        channel_config: dict,
    ) -> FormatOutput:
        """Run all LLM calls and return the FormatOutput.

        This method is called by the Celery worker BEFORE the video
        assembly pipeline. It must:
        1. Determine or generate a topic (if topic is None, pick one)
        2. Generate the narration script
        3. Generate SEO metadata
        4. Return a fully populated FormatOutput

        Args:
            topic: User-supplied topic string, or None for AI selection.
            channel_config: Dict with keys:
                - voice_id (str): ElevenLabs voice ID
                - music_category (str): Preferred music bucket
                - model_tier (str): "Lite" | "Balanced" | "Max"
                - duration (str): one of "20s" | "30s" | "60s" | "120s" | "150s"

        Returns:
            FormatOutput with all fields populated.
        """
        ...

    def get_pipeline_steps(self) -> list[str]:
        """Return the list of VideoPipeline steps this genre needs.

        Override to skip steps your genre does not use.
        Default returns the full Horror path.

        Available steps:
            "images"    - Generate images with Imagen 4 Fast (Horror)
            "footage"   - Pull a CC0 clip from assets/footage/<bucket> (Brainrot)
            "tts"       - Synthesize voice + word timestamps (ElevenLabs)
            "captions"  - Build captions from ElevenLabs timestamps (Whisper fallback)
            "assemble"  - Run FFmpeg assembly (visuals + mix + captions)

        For example, Brainrot returns ["footage", "tts", "captions", "assemble"]
        and skips image generation.
        """
        return ["images", "tts", "captions", "assemble"]

    def credit_cost(self, duration: str, model_tier: str) -> int:
        """Return the credits to debit for this generation run.

        Credits are the single user-facing unit. The real cost (images + voice,
        both duration-driven) is abstracted away. This delegates to the single
        source of truth in pricing.py — do NOT hardcode credit math here.

        Args:
            duration: one of "20s" | "30s" | "60s" | "120s" | "150s".
            model_tier: "Lite" | "Balanced" | "Max".

        Returns:
            Integer credit cost.
        """
        from app.core.pricing import credits_for_video
        return credits_for_video(duration, model_tier)
```

---

## Genre Config Schema

Each genre can declare a `config_schema` JSON object that describes its configurable options, rendered as a dynamic settings form in the dashboard. (No Reddit/subreddit options remain — topics come from the user, the channel topic queue, or a Gemini suggestion.)

Example schema for the Horror genre:

```json
{
  "type": "object",
  "properties": {
    "image_style": {
      "type": "string",
      "enum": ["cinematic", "found-footage", "illustrated"],
      "default": "cinematic",
      "description": "Visual style passed to the Imagen prompt"
    },
    "music_volume": {
      "type": "number",
      "minimum": 0.05,
      "maximum": 0.4,
      "default": 0.15,
      "description": "Background music volume (0.0 = silent, 1.0 = full)"
    }
  }
}
```

For the Brainrot genre, the equivalent schema selects a footage bucket
(`satisfying`, `parkour_clean`, `hydraulic`, `kinetic_sand`) instead of an image style.

---

## Plan Gating for Genres

The `min_plan` property controls which subscription tier is required to use a genre. The API enforces this when a generation request is received. Per-plan genre access (and the Lite/Balanced/Max model availability) is authoritative in `pricing.md`.

| Genre | Slug | Min Plan | Notes |
|---|---|---|---|
| Horror | `horror` | `free` | Free picks Horror **or** Brainrot (one, locked per channel) |
| Brainrot | `brainrot` | `free` | Free can choose this instead of Horror; Starter+ get both |
| Custom | `custom` | `pro` | User-defined genre; Pro & Agency only |

Users see locked genre cards in the dashboard with an upgrade prompt when their plan doesn't include a genre.

---

## Genre Registry

Genres are registered in `backend/app/services/formats/registry.py`. The registry maps slugs to handler instances:

```python
from app.services.formats.horror import HorrorPlugin
from app.services.formats.brainrot import BrainrotPlugin
from app.services.formats.custom import CustomPlugin

_REGISTRY: dict[str, FormatPlugin] = {
    "horror":   HorrorPlugin(),
    "brainrot": BrainrotPlugin(),
    "custom":   CustomPlugin(),
}


def get_format_plugin(slug: str) -> FormatPlugin:
    plugin = _REGISTRY.get(slug)
    if plugin is None:
        raise ValueError(f"Unknown genre slug: {slug!r}")
    return plugin


def list_formats() -> list[FormatPlugin]:
    return list(_REGISTRY.values())
```

The Celery worker resolves the handler from the channel's genre when a job is processed.

---

## Example: Implementing the Brainrot Genre

This walkthrough sketches the Brainrot handler, which uses **Gemini** for script + SEO, **ElevenLabs** for voice, and the **CC0 footage library** for visuals (no image generation). It is available from the Free plan up.

### Step 1: Create the Handler File

Create `backend/app/services/formats/brainrot.py`:

```python
from __future__ import annotations

import logging

from app.services.formats.base import FormatOutput, FormatPlugin
from app.services.llm.gemini import GeminiService   # the ONLY LLM service
from app.core.pricing import credits_for_video

logger = logging.getLogger(__name__)


class BrainrotPlugin(FormatPlugin):
    """Fast-paced narration over a satisfying CC0 footage loop.

    Pipeline: Gemini writes a punchy script AND the SEO metadata in the
    selected tier (Lite/Balanced/Max) → ElevenLabs synthesizes voice + word
    timestamps → a CC0 clip is pulled from assets/footage/<bucket> → captions
    from the timestamps → FFmpeg assembly. No Imagen, no stock-image vendor.
    """

    def __init__(self) -> None:
        self._gemini = GeminiService()

    @property
    def slug(self) -> str:
        return "brainrot"

    @property
    def name(self) -> str:
        return "Brainrot"

    @property
    def description(self) -> str:
        return "Punchy narration over satisfying CC0 footage loops."

    @property
    def min_plan(self) -> str:
        return "free"

    @property
    def default_music_category(self) -> str:
        return "upbeat_hype"

    def get_pipeline_steps(self) -> list[str]:
        # Footage instead of images; no Imagen call.
        return ["footage", "tts", "captions", "assemble"]

    async def prepare(
        self,
        topic: str | None,
        channel_config: dict,
    ) -> FormatOutput:
        model_tier = channel_config.get("model_tier", "Lite")
        duration = channel_config.get("duration", "30s")

        # 1. Topic: user-supplied, channel queue, or Gemini suggestion.
        if not topic:
            topic = await self._gemini.suggest_topic(genre="brainrot", tier=model_tier)

        # 2. Gemini generates BOTH the script and the SEO metadata in one place.
        result = await self._gemini.generate_script_and_seo(
            topic=topic, genre="brainrot", tier=model_tier, duration=duration,
        )

        return FormatOutput(
            script=result.script_text,
            seo_title=result.seo_title,
            seo_description=result.seo_description,
            seo_tags=result.seo_tags,
            voice_id=channel_config["voice_id"],            # ElevenLabs voice
            music_category=self.default_music_category,
            pipeline_steps=self.get_pipeline_steps(),
            credit_cost=credits_for_video(duration, model_tier),
        )
```

### Step 2: Register the Handler

Add it to `_REGISTRY` in `backend/app/services/formats/registry.py` (see the Genre Registry section above).

### Step 3: Seed the Footage Bucket

Brainrot reads CC0 clips from `assets/footage/<bucket>/`. Seed the bucket README placeholders and drop clips in:

```bash
bash scripts/seed_footage.sh          # buckets: satisfying, parkour_clean, hydraulic, kinetic_sand
# add .mp4 CC0 loops, then:
docker compose restart worker
```

### Step 4: Test

With the services running:

```bash
curl -X POST http://localhost:8000/api/v1/videos/generate \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "channel_id": "<your_channel_uuid>",
    "topic": "5 facts that will melt your brain",
    "model_tier": "Lite",
    "duration": "30s"
  }'
```

The genre is taken from the channel; check status via `GET /api/v1/videos/{job_id}`.

---

## Notes for Genre Authors

**Credits, not dollars:** Generation cost is debited in **credits** via `credits_for_video(duration, model_tier)` from `backend/app/core/pricing.py` — the single source of truth mirrored from `pricing.md`. Never hardcode credit or USD math in a handler.

**Gemini only:** Use `GeminiService` for both script and SEO. Do not reintroduce a second LLM. The model behind each tier is env-configured (`GEMINI_MODEL_LITE/BALANCED/MAX`).

**ElevenLabs only:** Voice always comes from ElevenLabs, which also returns the word timestamps captions depend on. Do not add edge-tts/Google TTS fallbacks.

**Visuals are genre-specific:** Horror generates images with Imagen; Brainrot pulls CC0 footage; custom genres choose one path. There is no stock-image vendor.

**Topic fallback is required:** `prepare()` must handle `topic=None` — use the channel's topic queue or a Gemini suggestion. There is no Reddit/trend source.

**Pipeline steps:** Only list the steps your genre uses (e.g. `"footage"` vs `"images"`) so the pipeline skips the others.
