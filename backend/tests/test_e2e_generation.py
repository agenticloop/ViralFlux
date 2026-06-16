"""Real end-to-end video generation tests (gated on real API keys).

For a MODEST matrix of (genre, duration, model, script_source) these run the
REAL pipeline — Gemini script + SEO, ElevenLabs TTS, Imagen/loop-footage visuals,
ffmpeg assembly — and assert a valid 1080x1920 MP4 with both a video and an audio
stream lands on disk and the job reaches a terminal-success status.

They SKIP cleanly when real keys are absent (placeholder dev .env), and RUN
automatically once real keys are present. Kept deliberately small to respect
ElevenLabs credit limits.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import uuid

import pytest
from sqlalchemy import select

from app.core import pricing
from app.core.config import settings
from app.core.database import async_session_maker
from app.models.channel import ChannelSchedule, YoutubeChannel
from app.models.user import User
from app.models.video_job import VideoJob
from app.workers.tasks.video_tasks import _generate_video_async


# --------------------------------------------------------------------------- gating
def _key_set(value: str | None) -> bool:
    if not value:
        return False
    lowered = value.lower()
    return not any(tok in lowered for tok in ("replace", "changeme", "your-", "xxxx"))


_KEYS_READY = _key_set(settings.GOOGLE_AI_API_KEY) and _key_set(settings.ELEVENLABS_API_KEY)

pytestmark = pytest.mark.skipif(
    not _KEYS_READY,
    reason="Real GOOGLE_AI_API_KEY / ELEVENLABS_API_KEY not configured",
)

# Where finished sample MP4s are copied for human review.
_SAMPLES_DIR = os.path.join(settings.MEDIA_DIR, "samples")


# --------------------------------------------------------------------------- helpers
def _ffprobe_streams(path: str) -> dict:
    """Return {'video': {...} | None, 'audio': {...} | None, 'duration': float}."""
    out = subprocess.run(
        [
            getattr(settings, "FFPROBE_PATH", None) or "ffprobe",
            "-v", "quiet", "-print_format", "json",
            "-show_format", "-show_streams", path,
        ],
        capture_output=True, text=True, timeout=30,
    )
    info = json.loads(out.stdout)
    video = audio = None
    for s in info.get("streams", []):
        if s.get("codec_type") == "video" and video is None:
            video = s
        elif s.get("codec_type") == "audio" and audio is None:
            audio = s
    duration = float(info.get("format", {}).get("duration", 0.0))
    return {"video": video, "audio": audio, "duration": duration}


async def _make_user(db, credits: int = 5000) -> User:
    """Create a verified user with a large credit balance (bypasses plan gating)."""
    u = User(
        email=f"e2e-{uuid.uuid4().hex[:12]}@example.com",
        password_hash="x",
        full_name="E2E User",
        is_verified=True,
        is_active=True,
        subscription_credits=credits,
        topup_credits=0,
    )
    db.add(u)
    await db.flush()
    return u


async def _make_channel(db, user: User, genre: str) -> YoutubeChannel:
    cfg_voice = {
        "horror": "pqHfZKP75CvOlQylNhV4",
        "brainrot": "pNInz6obpgDQGcFmaJgB",
        "custom": "VR6AewLTigWG4xSOukaG",
    }[genre]
    music = {"horror": "horror_ambient", "brainrot": "upbeat_hype", "custom": "cinematic_epic"}[genre]
    ch = YoutubeChannel(
        user_id=user.id,
        channel_name=f"E2E {genre}",
        genre=genre,
        seed_prompt={
            "horror": "an abandoned hospital at night",
            "brainrot": "the most oddly satisfying facts ever",
            "custom": "incredible facts about deep space",
        }[genre],
        voice_id=cfg_voice,
        music_bucket=music,
    )
    db.add(ch)
    await db.flush()
    # Schedule with require_approval=True so a successful job lands in
    # pending_approval (no YouTube upload attempted).
    db.add(ChannelSchedule(channel_id=ch.id, require_approval=True))
    await db.flush()
    return ch


async def _make_job(db, user, channel, *, genre, duration, model, script_source,
                    script=None, topic=None) -> VideoJob:
    job = VideoJob(
        user_id=user.id,
        channel_id=channel.id,
        genre=genre,
        duration_tier=duration,
        model_tier=model,
        script_source=script_source,
        status="queued",
        topic=topic,
        script=script,
        voice_id=channel.voice_id,
        credits_cost=pricing.credits_for_video(duration, model),
    )
    db.add(job)
    await db.flush()
    return job


async def _run_combo(*, genre, duration, model, script_source, script=None,
                     topic=None, sample_name=None):
    """Create rows, run the real pipeline, return the reloaded job."""
    async with async_session_maker() as db:
        user = await _make_user(db)
        channel = await _make_channel(db, user, genre)
        job = await _make_job(
            db, user, channel,
            genre=genre, duration=duration, model=model,
            script_source=script_source, script=script, topic=topic,
        )
        await db.commit()
        job_id = str(job.id)

    # Run the real generation coroutine exactly as the Celery task would.
    await _generate_video_async(job_id)

    async with async_session_maker() as db:
        res = await db.execute(select(VideoJob).where(VideoJob.id == uuid.UUID(job_id)))
        job = res.scalar_one()

    # Surface the failure reason if generation did not succeed.
    assert job.status in ("pending_approval", "approved", "posted"), (
        f"{genre}/{duration}/{model} failed: status={job.status} "
        f"error={job.error_message}"
    )

    assert job.video_path and os.path.isfile(job.video_path), (
        f"video_path missing on disk: {job.video_path}"
    )

    streams = _ffprobe_streams(job.video_path)
    assert streams["video"] is not None, "MP4 has no video stream"
    assert streams["audio"] is not None, "MP4 has no audio stream"
    assert (streams["video"]["width"], streams["video"]["height"]) == (1080, 1920), (
        f"unexpected resolution: {streams['video']['width']}x{streams['video']['height']}"
    )

    # Duration check.
    #  - For AI/seed scripts the model targets the tier length, so assert the
    #    rendered video lands within a wide band of the tier target.
    #  - For MANUAL scripts the length follows the USER's text (the tier only
    #    caps the char budget), so assert against the script's natural narration
    #    length (~15 chars/sec) instead of the tier target.
    if script_source == "manual":
        expected = max(3.0, len(job.script) / 15.0)
        assert streams["duration"] >= expected * 0.5, (
            f"manual duration {streams['duration']:.1f}s far below "
            f"script-implied {expected:.1f}s"
        )
    else:
        target = pricing.DURATION_SECONDS[duration]
        assert streams["duration"] >= target * 0.5, (
            f"duration {streams['duration']:.1f}s far below target {target}s"
        )
        assert streams["duration"] <= target * 1.6, (
            f"duration {streams['duration']:.1f}s far above target {target}s"
        )

    # Script present and within the plan char budget.
    assert job.script and job.script.strip(), "job.script empty"
    char_limit = pricing.DURATION_CHARS[duration]
    assert len(job.script) <= char_limit + 50, (
        f"script {len(job.script)} chars exceeds budget {char_limit}"
    )

    # Copy a sample for human review.
    if sample_name:
        os.makedirs(_SAMPLES_DIR, exist_ok=True)
        shutil.copy2(job.video_path, os.path.join(_SAMPLES_DIR, sample_name))

    return job


# --------------------------------------------------------------------------- matrix
async def test_e2e_horror_20s_lite_ai():
    job = await _run_combo(
        genre="horror", duration="20s", model="Lite", script_source="ai",
        topic="an abandoned subway station at 3am",
        sample_name="horror_20s.mp4",
    )
    # ElevenLabs with-timestamps should populate word_timestamps.
    assert job.word_timestamps and job.word_timestamps.get("words")


async def test_e2e_horror_60s_max_manual():
    manual = (
        "I found the door at the end of the hall. It had no handle, only a keyhole "
        "weeping cold air. I pressed my eye to it and saw my own bedroom, my own bed, "
        "and something sitting at the foot of it, watching the door. Watching me watch it. "
        "I have not slept since. The keyhole is gone now, but every night I hear it breathing."
    )
    await _run_combo(
        genre="horror", duration="60s", model="Max", script_source="manual",
        script=manual,
    )


async def test_e2e_brainrot_30s_lite_seed():
    await _run_combo(
        genre="brainrot", duration="30s", model="Lite", script_source="seed",
        topic="oddly satisfying facts about the human body",
        sample_name="brainrot_30s.mp4",
    )


async def test_e2e_brainrot_60s_balanced_ai():
    await _run_combo(
        genre="brainrot", duration="60s", model="Balanced", script_source="ai",
        topic="mind-blowing facts that sound fake but are true",
    )


async def test_e2e_custom_30s_balanced_ai():
    await _run_combo(
        genre="custom", duration="30s", model="Balanced", script_source="ai",
        topic="the strangest objects ever found in deep space",
        sample_name="custom_30s.mp4",
    )


async def test_e2e_horror_30s_lite_ai():
    await _run_combo(
        genre="horror", duration="30s", model="Lite", script_source="ai",
        topic="a lighthouse keeper's last radio transmission",
    )
