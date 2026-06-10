# ViralFlux — Format Plugin Documentation

ViralFlux is built around a pluggable content format system. Every type of YouTube Short is implemented as a **Format Plugin** — a self-contained class that knows how to generate a script, select media assets, configure audio, and estimate its own cost. The core video pipeline is format-agnostic; it delegates all content decisions to the active plugin.

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
    voice_provider: str            # e.g., "edge-tts", "elevenlabs", "google-tts"
    voice_id: str                  # Provider-specific voice ID
    music_category: str            # Music folder slug (e.g., "horror_ambient")
    pipeline_steps: list[str]      # Steps the video pipeline should run
    cost_estimate_usd: Decimal     # Estimated LLM + TTS cost for this job


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
        """Minimum plan slug required to use this format.
        
        One of: 'starter', 'creator', 'agency'.
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
                - voice_provider (str): TTS provider for this channel
                - voice_id (str): TTS voice ID
                - music_category (str): Preferred music category
        
        Returns:
            FormatOutput with all fields populated.
        """
        ...

    def get_pipeline_steps(self) -> list[str]:
        """Return the list of VideoPipeline steps this format needs.
        
        Override to skip steps your format does not use.
        Default returns all steps.

        Available steps:
            "images"    - Fetch stock images from Pexels/Pixabay
            "tts"       - Synthesize voice audio from script
            "captions"  - Generate SRT from voice audio (Whisper)
            "assemble"  - Run FFmpeg assembly (Ken Burns + concat + mix + captions)

        For example, a text-overlay-only format might return ["tts", "assemble"]
        and skip image sourcing.
        """
        return ["images", "tts", "captions", "assemble"]

    def estimate_cost(self, script_char_count: int, voice_provider: str) -> Decimal:
        """Estimate the USD cost for this generation run.
        
        Default implementation uses standard per-provider rates.
        Override if your format uses additional paid APIs.
        
        Args:
            script_char_count: Character count of the generated script.
            voice_provider: TTS provider being used.
        
        Returns:
            Estimated cost in USD as a Decimal.
        """
        tts_cost_per_char = {
            "elevenlabs": Decimal("0.00000033"),   # ~$0.003 per 900-char script
            "google-tts": Decimal("0.000004"),     # $4 per 1M chars
            "edge-tts":   Decimal("0"),            # Free
        }
        llm_cost = Decimal("0.0015")               # Gemini script + GPT-4o-mini SEO
        tts_cost = tts_cost_per_char.get(
            voice_provider, Decimal("0")
        ) * script_char_count
        return llm_cost + tts_cost
```

---

## Format Config Schema

Each format can declare a `config_schema` JSON object that describes its configurable options. This schema is stored in the `content_formats.config_schema` database column and used to render a dynamic settings form in the dashboard.

Example schema for the horror story format:

```json
{
  "type": "object",
  "properties": {
    "subreddits": {
      "type": "array",
      "items": { "type": "string" },
      "default": ["nosleep", "creepypasta", "LetsNotMeet"],
      "description": "Subreddits to scrape for story candidates"
    },
    "max_words": {
      "type": "integer",
      "minimum": 100,
      "maximum": 200,
      "default": 160,
      "description": "Maximum word count for generated scripts"
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

---

## Plan Gating for Formats

The `min_plan` property on each plugin controls which subscription tier is required to use the format. The API enforces this check when a video generation request is received.

| Format | Slug | Min Plan | Status |
|---|---|---|---|
| Horror Story Shorts | `horror_story` | `starter` | Active (Phase 1) |
| Brainrot Dialogue | `brainrot` | `creator` | Planned (Phase 2) |
| Ranking / Listicle | `ranking` | `creator` | Planned (Phase 2) |
| Motivational Quotes | `motivational` | `creator` | Planned (Phase 2) |
| Clip Stitch Commentary | `clip_stitch` | `agency` | Planned (Phase 2) |

Users on the Starter plan see locked format cards in the dashboard with an "Upgrade to Creator" prompt.

---

## Format Registry

Formats are registered in `backend/app/services/formats/registry.py`. The registry maps slugs to plugin instances:

```python
from app.services.formats.horror_story import HorrorStoryPlugin
from app.services.formats.brainrot import BrainrotPlugin

_REGISTRY: dict[str, FormatPlugin] = {
    "horror_story": HorrorStoryPlugin(),
    "brainrot":     BrainrotPlugin(),
}


def get_format_plugin(slug: str) -> FormatPlugin:
    plugin = _REGISTRY.get(slug)
    if plugin is None:
        raise ValueError(f"Unknown format slug: {slug!r}")
    return plugin


def list_formats() -> list[FormatPlugin]:
    return list(_REGISTRY.values())
```

The Celery worker calls `get_format_plugin(job.format_slug)` when a job is processed.

---

## Example: Implementing a "News Summary" Format

This walkthrough creates a new format that summarizes trending news stories as punchy 60-second YouTube Shorts. The format is gated to the Creator plan.

### Step 1: Create the Plugin File

Create `backend/app/services/formats/news_summary.py`:

```python
from __future__ import annotations

import logging
from decimal import Decimal

from app.services.formats.base import FormatOutput, FormatPlugin
from app.services.llm.gemini import GeminiService
from app.services.llm.openai_svc import OpenAIService

logger = logging.getLogger(__name__)


class NewsSummaryPlugin(FormatPlugin):
    """Summarizes a trending news story as a punchy YouTube Short.
    
    Pipeline: fetch headline → Gemini rewrites as hook-driven script →
    GPT-4o-mini generates SEO → edge-tts voice (fast, neutral) →
    Pexels stock images → captions → final video.
    """

    def __init__(self) -> None:
        self._gemini = GeminiService()
        self._openai = OpenAIService()

    @property
    def slug(self) -> str:
        return "news_summary"

    @property
    def name(self) -> str:
        return "News Summary Shorts"

    @property
    def description(self) -> str:
        return "Turn trending news stories into punchy 60-second Shorts."

    @property
    def min_plan(self) -> str:
        return "creator"

    @property
    def default_music_category(self) -> str:
        return "cinematic_epic"

    async def prepare(
        self,
        topic: str | None,
        channel_config: dict,
    ) -> FormatOutput:
        # 1. Determine topic
        if not topic:
            # In a full implementation, call a news API here.
            # For now, Gemini suggests a topic.
            topic = "Breaking: Major tech company announces AI breakthrough"

        # 2. Generate script — reuse Gemini with a news-specific prompt
        script_result = await self._generate_news_script(topic)

        # 3. Generate SEO metadata
        seo_result = await self._openai.generate_seo(
            script=script_result.script_text,
            topic=topic,
            format_slug=self.slug,
        )

        # 4. Determine voice — news works best with a clear neutral voice
        voice_provider = channel_config.get("voice_provider", "edge-tts")
        voice_id = channel_config.get("voice_id", "en-US-AriaNeural")

        cost = self.estimate_cost(len(script_result.script_text), voice_provider)

        return FormatOutput(
            script=script_result.script_text,
            seo_title=seo_result.title,
            seo_description=seo_result.description,
            seo_tags=seo_result.tags,
            voice_provider=voice_provider,
            voice_id=voice_id,
            music_category=self.default_music_category,
            pipeline_steps=self.get_pipeline_steps(),
            cost_estimate_usd=cost,
        )

    async def _generate_news_script(self, topic: str):
        """Generate a news-style narration script using Gemini."""
        import google.generativeai as genai
        from app.core.config import settings

        genai.configure(api_key=settings.GOOGLE_AI_API_KEY)
        model = genai.GenerativeModel(settings.GEMINI_MODEL)

        prompt = f"""Write a YouTube Shorts news narration script (max 140 words) about:

Topic: {topic}

Rules:
1. Open with the most shocking fact — ≤12 words
2. Three punchy supporting facts (one sentence each)
3. Close with the implication / what happens next
4. Neutral, authoritative tone — no opinions
5. Target: 45–55 seconds at news-anchor pace

Return ONLY valid JSON:
{{
  "script_text": "<full narration>",
  "hook_line": "<opening sentence>",
  "estimated_duration_sec": <integer 45–55>
}}"""

        import json, re

        response = await model.generate_content_async(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.5,
                max_output_tokens=400,
            ),
        )

        # Strip code fences and parse
        text = re.sub(r"^```(?:json)?\s*", "", response.text.strip())
        text = re.sub(r"\s*```$", "", text)
        data = json.loads(text)

        from app.services.llm.base import ScriptResult
        return ScriptResult(
            script_text=data["script_text"],
            estimated_duration_sec=int(data["estimated_duration_sec"]),
            hook_line=data["hook_line"],
        )
```

### Step 2: Register the Plugin

Open `backend/app/services/formats/registry.py` and add the import and registration:

```python
from app.services.formats.news_summary import NewsSummaryPlugin   # add this line

_REGISTRY: dict[str, FormatPlugin] = {
    "horror_story": HorrorStoryPlugin(),
    "brainrot":     BrainrotPlugin(),
    "news_summary": NewsSummaryPlugin(),                           # add this line
}
```

### Step 3: Add a Database Row for the Format

The `content_formats` table tracks which formats exist and their metadata. Add a row in the seed script or via migration:

```sql
INSERT INTO content_formats (slug, name, description, is_active, min_plan, config_schema)
VALUES (
  'news_summary',
  'News Summary Shorts',
  'Turn trending news stories into punchy 60-second Shorts.',
  TRUE,
  'creator',
  '{"type":"object","properties":{"news_sources":{"type":"array","default":["reuters","apnews"]}}}'
);
```

Alternatively, add it to `backend/app/seed.py` in the formats list.

### Step 4: Add a Music Category (Optional)

If your format uses a new music category, create the assets directory and add the README placeholder:

```bash
mkdir -p assets/music/news_dramatic
# Add royalty-free .mp3 files or see seed_music.sh
```

### Step 5: Test the New Format

With the services running:

```bash
# Queue a test video using the new format
curl -X POST http://localhost/api/v1/videos/generate \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "channel_id": "<your_channel_uuid>",
    "format": "news_summary",
    "topic": "Scientists discover new species in deep ocean trench"
  }'
```

Check the job status in the dashboard or via `GET /api/v1/videos/{job_id}`.

---

## Notes for Format Authors

**Cost discipline:** The `estimate_cost()` method is called before generation begins and is shown in the dashboard. If your format uses additional paid APIs (image generation, video APIs, etc.), override `estimate_cost()` to include those costs.

**Keep plugins independent:** Plugins should not import from other plugin files. Shared utilities belong in `backend/app/services/` top-level modules.

**Respect plan gating:** The `min_plan` property is checked by the API before the plugin is invoked. If your format uses expensive APIs, gate it to Creator or Agency.

**Topic fallback is required:** `prepare()` must handle `topic=None` gracefully. Either call an API to discover a trending topic, use Gemini to generate one, or fall back to a hardcoded default.

**Pipeline steps:** Only list the steps your format actually uses. A format with no images should not list `"images"` in `get_pipeline_steps()` — this avoids unnecessary Pexels API calls.
