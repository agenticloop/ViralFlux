"""Tests that hit real external providers (Gemini / ElevenLabs / Imagen).

These SKIP cleanly when no real key is configured (the dev .env ships
placeholder keys like 'replace-with-...'), and RUN automatically once real keys
are added. They assert the integration contract, not deterministic content.
"""
from __future__ import annotations

import tempfile

import pytest

from app.core import pricing
from app.core.config import settings


def _key_set(value: str | None) -> bool:
    """A key is 'real' only if it's non-empty and not an obvious placeholder."""
    if not value:
        return False
    lowered = value.lower()
    return not any(tok in lowered for tok in ("replace", "changeme", "your-", "xxxx"))


_GEMINI = _key_set(settings.GOOGLE_AI_API_KEY)
_ELEVEN = _key_set(settings.ELEVENLABS_API_KEY)
# Imagen rides on the Google AI Studio key.
_IMAGEN = _GEMINI


@pytest.mark.skipif(not _GEMINI, reason="GOOGLE_AI_API_KEY not configured (real key)")
async def test_gemini_generate_script_returns_scriptresult():
    from app.services.llm.base import ScriptResult
    from app.services.llm.gemini import gemini_service

    char_limit = pricing.PLAN_SCRIPT_CHAR_LIMIT["free"]
    result = await gemini_service.generate_script(
        genre="horror",
        seed="an abandoned subway station",
        duration_tier="20s",
        model_tier="Lite",
        char_limit=char_limit,
    )
    assert isinstance(result, ScriptResult)
    assert result.script
    assert len(result.script) <= char_limit
    assert len(result.scenes) >= 1
    assert all("text" in s for s in result.scenes)


@pytest.mark.skipif(not _ELEVEN, reason="ELEVENLABS_API_KEY not configured (real key)")
async def test_elevenlabs_synthesize_returns_ttsresult():
    from app.core.genres import voice_settings_for
    from app.services.tts.base import TTSResult
    from app.services.tts.elevenlabs import elevenlabs_service

    with tempfile.TemporaryDirectory() as d:
        out = f"{d}/out.mp3"
        result = await elevenlabs_service.synthesize(
            text="The lights went out, one by one.",
            voice_id="pqHfZKP75CvOlQylNhV4",  # Bill (horror default)
            voice_settings=voice_settings_for("horror"),
            out_path=out,
        )
        assert isinstance(result, TTSResult)
        assert result.audio_path
        assert result.char_count > 0
        # with-timestamps endpoint should yield word-level alignment.
        assert isinstance(result.word_timestamps, list)


@pytest.mark.skipif(not _IMAGEN, reason="Image provider key not configured (real key)")
async def test_image_service_generates_scene_images():
    import os

    from app.services.assets.image_service import image_service

    with tempfile.TemporaryDirectory() as d:
        prompts = [
            "cinematic horror, a dark empty hallway, film grain, 9:16 vertical",
            "cinematic horror, a flickering ceiling light, eerie, 9:16 vertical",
        ]
        paths = await image_service.generate_scene_images(prompts, seed=42, out_dir=d)
        assert len(paths) == len(prompts)
        assert all(os.path.exists(p) for p in paths)
