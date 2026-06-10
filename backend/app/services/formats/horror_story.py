from __future__ import annotations

import logging
import re

from .base import FormatPlugin, FormatOutput

logger = logging.getLogger(__name__)

# Common English stop-words to filter out when extracting keywords
_STOP_WORDS = frozenset(
    """
    a an the and but or so yet for nor as at by in of on to up
    be is are was were been being have has had do does did will
    would could should may might must shall can need dare ought
    i me my myself we our ours ourselves you your yours yourself
    he him his himself she her hers herself it its itself they
    them their theirs themselves what which who whom this that
    these those am not no yes just with from out if then there
    here when where why how all both each few more most other
    some such than too very
    """.split()
)


def _extract_keywords(text: str, top_n: int = 5) -> list[str]:
    """Extract the top_n most frequent non-stop nouns/content words from text.

    Uses a simple split-and-filter heuristic (no external NLP lib required).
    """
    # Lowercase, remove punctuation
    cleaned = re.sub(r"[^a-zA-Z\s]", " ", text.lower())
    tokens = cleaned.split()

    freq: dict[str, int] = {}
    for tok in tokens:
        if len(tok) >= 4 and tok not in _STOP_WORDS:
            freq[tok] = freq.get(tok, 0) + 1

    sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return [w for w, _ in sorted_words[:top_n]]


class HorrorStoryFormat(FormatPlugin):
    """Horror story narration format — the core ViralFlux format.

    Uses Gemini for script generation and OpenAI for SEO metadata.
    Falls back to EdgeTTS (free) unless the channel overrides voice settings.
    """

    slug = "horror_story"
    name = "Horror Story Narration"
    min_plan = "starter"

    async def prepare(
        self,
        topic: str | None,
        channel_config: dict,
    ) -> FormatOutput:
        """Build a complete FormatOutput for a horror shorts video.

        1. Discover topic via Reddit if not provided.
        2. Generate script via Gemini.
        3. Generate SEO via OpenAI.
        4. Extract image-search keywords.
        5. Return FormatOutput with voice/music defaults.
        """
        from app.services.llm.gemini import GeminiService
        from app.services.llm.openai_svc import OpenAIService
        from app.services.reddit_service import RedditService
        from app.core.config import settings

        # ----------------------------------------------------------
        # Step 1: Topic discovery
        # ----------------------------------------------------------
        source_url = ""
        if not topic:
            logger.info("No topic provided — fetching trending posts from Reddit.")
            reddit = RedditService(
                client_id=settings.REDDIT_CLIENT_ID,
                client_secret=settings.REDDIT_CLIENT_SECRET,
                user_agent=settings.REDDIT_USER_AGENT,
            )
            candidates = reddit.get_trending_posts(limit=10)
            if candidates:
                gemini = GeminiService()
                topic_result = await gemini.pick_topic(candidates)
                topic = topic_result.recommended_topic
                source_url = topic_result.source_url
                # Use the actual post text as the raw story if we can find it
                for c in candidates:
                    if c["title"] == topic:
                        topic = c["text"] or topic
                        break
                logger.info("Selected topic: %s (confidence=%.2f)", topic, topic_result.confidence_score)
            else:
                topic = "A terrifying encounter in an abandoned house"
                logger.warning("No Reddit candidates found; using fallback topic.")

        # ----------------------------------------------------------
        # Step 2: Script generation (Gemini)
        # ----------------------------------------------------------
        gemini = GeminiService()
        script_result = await gemini.generate_script(
            raw_story=topic,
            format_slug=self.slug,
        )
        logger.info(
            "Script generated: %d chars, ~%ds",
            len(script_result.script_text),
            script_result.estimated_duration_sec,
        )

        # ----------------------------------------------------------
        # Step 3: SEO generation (OpenAI)
        # ----------------------------------------------------------
        openai_svc = OpenAIService()
        seo_result = await openai_svc.generate_seo(
            script=script_result.script_text,
            topic=topic[:200],
            format_slug=self.slug,
        )

        # ----------------------------------------------------------
        # Step 4: Image search keywords
        # ----------------------------------------------------------
        keywords = _extract_keywords(script_result.script_text, top_n=5)
        if not keywords:
            keywords = ["horror", "dark", "abandoned"]

        # ----------------------------------------------------------
        # Step 5: Voice & music config (channel overrides or defaults)
        # ----------------------------------------------------------
        voice_provider = channel_config.get("voice_provider") or "edge-tts"
        voice_id = channel_config.get("voice_id") or "en-US-GuyNeural"

        # ----------------------------------------------------------
        # Step 6: Cost estimate
        # ----------------------------------------------------------
        char_count = len(script_result.script_text)
        cost = self.estimate_cost(char_count)

        return FormatOutput(
            script=script_result.script_text,
            hook_line=script_result.hook_line,
            estimated_duration_sec=script_result.estimated_duration_sec,
            seo_title=seo_result.title,
            seo_description=seo_result.description,
            seo_tags=seo_result.tags,
            hashtags=seo_result.hashtags,
            thumbnail_text=seo_result.thumbnail_text,
            keywords=keywords,
            voice_provider=voice_provider,
            voice_id=voice_id,
            music_category="horror_ambient",
            cost_estimate_usd=cost,
        )

    def estimate_cost(self, char_count: int) -> float:
        """Estimate cost in USD.

        TTS cost (edge-tts = free by default) + fixed LLM cost estimate of $0.002.
        If a paid TTS provider is used the caller should override this.
        """
        tts_cost = 0.0  # EdgeTTS default is free
        llm_fixed = 0.002
        return round(tts_cost + llm_fixed, 6)
