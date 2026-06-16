from __future__ import annotations

import asyncio
import logging
import os
import shutil
import uuid
from pathlib import Path

from app.core.config import settings
from app.core import pricing

from .ffmpeg_utils import FFmpegUtils, VideoProcessingError

logger = logging.getLogger(__name__)


class VideoPipeline:
    """Assembles a finished 1080x1920 short from a prepared FormatOutput.

    Steps:
      1. TTS narration (ElevenLabs).
      2. Visuals — generated images + ken-burns, or a CC0 loop trimmed to length.
      3. Captions — word-by-word ASS (ElevenLabs timestamps, whisper fallback).
      4. Audio — ducked music mixed under narration.
      5. Assemble + burn captions → MEDIA_DIR/previews/{job.id}.mp4.

    Resilient: missing music/footage degrades gracefully; only TTS/assembly
    failures are fatal.
    """

    def __init__(self) -> None:
        self.ffmpeg = FFmpegUtils(
            getattr(settings, "FFMPEG_PATH", "/usr/bin/ffmpeg"),
            getattr(settings, "FFPROBE_PATH", None),
        )

    async def run(self, job, channel, fmt) -> dict:
        """Render the video. Returns {video_path, cost_usd, word_timestamps, duration_sec}."""
        job_id = str(getattr(job, "id", uuid.uuid4()))
        duration_tier = getattr(job, "duration_tier", None) or "30s"
        target_sec = pricing.DURATION_SECONDS.get(duration_tier, 30)

        tmp_dir = os.path.join("/tmp", f"viralflux_{job_id}")
        Path(tmp_dir).mkdir(parents=True, exist_ok=True)
        logger.info("[%s] Pipeline start (tmp=%s)", job_id, tmp_dir)

        loop = asyncio.get_running_loop()
        try:
            # --- 1. TTS ---
            audio_path = os.path.join(tmp_dir, "voice.mp3")
            tts = await self._tts(fmt, audio_path)
            cost_usd = float(getattr(tts, "cost_usd", 0.0) or 0.0)
            word_timestamps = list(getattr(tts, "word_timestamps", []) or [])

            voice_sec = self._safe_duration(getattr(tts, "audio_path", audio_path)) or target_sec

            # --- 2. Visuals → silent video at voice length ---
            silent_video = os.path.join(tmp_dir, "silent.mp4")
            image_cost = await self._build_visuals(
                job, fmt, tmp_dir, silent_video, voice_sec, loop
            )
            cost_usd += image_cost

            # --- 3. Captions (ASS) ---
            ass_path = await self._build_captions(
                fmt, word_timestamps, getattr(tts, "audio_path", audio_path),
                tmp_dir, loop,
            )

            # --- 4. Audio mix (ducked music under narration) ---
            mixed = os.path.join(tmp_dir, "mixed.mp4")
            music_path = self._pick_music(fmt.music_bucket)
            await loop.run_in_executor(
                None,
                lambda: self.ffmpeg.mix_audio(
                    silent_video,
                    getattr(tts, "audio_path", audio_path),
                    music_path,
                    mixed,
                ),
            )

            # --- 5. Burn captions + finalize ---
            final_src = mixed
            if ass_path and os.path.isfile(ass_path) and os.path.getsize(ass_path) > 0:
                captioned = os.path.join(tmp_dir, "captioned.mp4")
                try:
                    await loop.run_in_executor(
                        None,
                        lambda: self.ffmpeg.burn_subtitles(mixed, ass_path, captioned),
                    )
                    final_src = captioned
                except VideoProcessingError as exc:
                    logger.warning("[%s] Caption burn failed, shipping uncaptioned: %s", job_id, exc)

            final_path = self._final_path(job_id)
            await loop.run_in_executor(None, shutil.copy2, final_src, final_path)
            duration_sec = self._safe_duration(final_path) or voice_sec

            logger.info("[%s] Pipeline complete → %s (%.1fs, $%.4f)",
                        job_id, final_path, duration_sec, cost_usd)
            return {
                "video_path": final_path,
                "cost_usd": round(cost_usd, 6),
                "word_timestamps": word_timestamps,
                "duration_sec": round(duration_sec, 2),
            }
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    # ------------------------------------------------------------------
    # Steps
    # ------------------------------------------------------------------

    async def _tts(self, fmt, out_path: str):
        from app.services.tts import elevenlabs_service

        script = (fmt.script or "").strip()
        if not script:
            raise VideoProcessingError("Cannot run TTS: FormatOutput has empty script.")
        return await elevenlabs_service.synthesize(
            text=script,
            voice_id=fmt.voice_id,
            voice_settings=fmt.voice_settings,
            out_path=out_path,
        )

    async def _build_visuals(
        self, job, fmt, tmp_dir: str, out_path: str, voice_sec: float, loop
    ) -> float:
        """Build the silent 1080x1920 video track. Returns image cost estimate."""
        from app.services.assets import image_service, footage_library
        from app.core import genres as genres_mod

        image_cost = 0.0

        if fmt.visual == genres_mod.VISUAL_GENERATED:
            seed = self._seed(job)
            img_dir = os.path.join(tmp_dir, "images")
            os.makedirs(img_dir, exist_ok=True)
            prompts = fmt.image_prompts or [p for p in (s.get("image_prompt") for s in fmt.scenes) if p]
            image_paths = await image_service.generate_scene_images(
                prompts=prompts, seed=seed, out_dir=img_dir
            )
            if not image_paths:
                raise VideoProcessingError("No scene images were generated.")

            image_cost = round(0.04 * len(image_paths), 6)  # rough per-image estimate

            per = max(1.0, voice_sec / len(image_paths))
            clip_paths: list[str] = []
            for i, img in enumerate(image_paths):
                resized = os.path.join(tmp_dir, f"resized_{i}.jpg")
                clip = os.path.join(tmp_dir, f"clip_{i}.mp4")
                await loop.run_in_executor(None, self.ffmpeg.resize_image, img, resized)
                await loop.run_in_executor(
                    None,
                    lambda r=resized, c=clip, d=per: self.ffmpeg.ken_burns(r, c, duration=d),
                )
                clip_paths.append(clip)
            await loop.run_in_executor(
                None, lambda: self.ffmpeg.concat_clips(clip_paths, out_path)
            )
        else:
            # loop_footage — footage_bucket is the CC0 clip bucket (e.g.
            # "satisfying"), distinct from the music_bucket (e.g. "upbeat_hype").
            bucket = getattr(fmt, "footage_bucket", None) or fmt.music_bucket
            # A single short loop is fine: footage is looped to length, so don't
            # demand a clip that's already >= the full narration.
            footage = footage_library.pick_loop(bucket) or footage_library.pick_loop(
                bucket, min_seconds=voice_sec
            )
            if not footage:
                raise VideoProcessingError(
                    f"No loop footage available for bucket '{bucket}'."
                )
            await loop.run_in_executor(
                None, lambda: self.ffmpeg.loop_footage(footage, out_path, voice_sec)
            )

        return image_cost

    async def _build_captions(
        self, fmt, word_timestamps, audio_path, tmp_dir, loop
    ) -> str | None:
        from app.services.video.captions import build_ass, build_ass_from_whisper

        ass_path = os.path.join(tmp_dir, "captions.ass")
        try:
            if word_timestamps:
                await loop.run_in_executor(
                    None,
                    lambda: build_ass(word_timestamps, fmt.caption_style, ass_path),
                )
            else:
                await loop.run_in_executor(
                    None,
                    lambda: build_ass_from_whisper(audio_path, fmt.caption_style, ass_path),
                )
            return ass_path
        except Exception as exc:
            logger.warning("Caption build failed; proceeding without captions: %s", exc)
            return None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _pick_music(self, bucket: str) -> str | None:
        try:
            from app.services.assets import music_library

            return music_library.pick_track(bucket)
        except Exception as exc:
            logger.warning("Music pick failed for bucket '%s': %s", bucket, exc)
            return None

    def _final_path(self, job_id: str) -> str:
        dest_dir = os.path.join(settings.MEDIA_DIR, "previews")
        os.makedirs(dest_dir, exist_ok=True)
        return os.path.join(dest_dir, f"{job_id}.mp4")

    def _safe_duration(self, path: str) -> float | None:
        try:
            if path and os.path.isfile(path):
                return self.ffmpeg.get_duration(path)
        except VideoProcessingError:
            pass
        return None

    def _seed(self, job) -> int:
        raw = str(getattr(job, "id", "") or "")
        digits = "".join(c for c in raw if c.isdigit())
        return int(digits[:9]) if digits else abs(hash(raw)) % (10**9)
