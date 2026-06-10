from __future__ import annotations

import asyncio
import logging
import os
import shutil
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from .ffmpeg_utils import FFmpegUtils, VideoProcessingError
from .whisper_svc import WhisperService

logger = logging.getLogger(__name__)


@dataclass
class PipelineContext:
    job_id: str
    tmp_dir: str           # /tmp/{job_id}/
    voice_path: str        # tmp_dir/voice.mp3
    srt_path: str          # tmp_dir/captions.srt
    music_path: str        # selected from assets (may be empty string)
    image_paths: list[str] = field(default_factory=list)   # tmp_dir/img_0.jpg …
    clip_paths: list[str] = field(default_factory=list)    # tmp_dir/clip_0.mp4 …
    concat_path: str = ""  # tmp_dir/concat.mp4
    mixed_path: str = ""   # tmp_dir/mixed.mp4
    final_path: str = ""   # media/previews/{job_id}.mp4


class VideoPipeline:
    """Orchestrates the full short-video production pipeline.

    Steps:
      1. TTS  — generate narration audio
      2. Images — fetch stock images matching the topic keywords
      3. Captions — transcribe audio → SRT
      4. Assemble — resize images, ken-burns, concat, mix audio, burn subs
      5. Move — copy final MP4 to media/previews/
    """

    def __init__(self, settings, db_session) -> None:
        self.settings = settings
        self.db = db_session
        self.ffmpeg = FFmpegUtils(settings.FFMPEG_PATH)
        self.whisper = WhisperService(settings.WHISPER_MODEL)

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    async def run(self, job) -> str:
        """Run the full pipeline for a VideoJob. Returns final video path."""
        ctx = self._make_context(job)
        Path(ctx.tmp_dir).mkdir(parents=True, exist_ok=True)
        logger.info("[%s] Pipeline started. tmp_dir=%s", ctx.job_id, ctx.tmp_dir)

        try:
            await self._step_tts(job, ctx)
            await self._step_fetch_images(job, ctx)
            await self._step_captions(ctx)
            await self._step_assemble(job, ctx)
            await self._step_move_to_media(ctx)
            logger.info("[%s] Pipeline complete → %s", ctx.job_id, ctx.final_path)
            return ctx.final_path
        except Exception:
            logger.exception("[%s] Pipeline failed.", ctx.job_id)
            raise
        finally:
            self._cleanup_tmp(ctx)

    # ------------------------------------------------------------------
    # Pipeline steps
    # ------------------------------------------------------------------

    async def _step_tts(self, job, ctx: PipelineContext) -> None:
        """Synthesise narration audio from the job script."""
        logger.info("[%s] Step 1/5: TTS synthesis", ctx.job_id)

        from app.services.tts import get_tts_service

        provider = getattr(job, "voice_provider", None) or "edge-tts"
        voice_id = getattr(job, "voice_id", None) or "en-US-GuyNeural"
        script_text = getattr(job, "script_text", "") or ""

        if not script_text.strip():
            raise VideoProcessingError(
                f"[{ctx.job_id}] Cannot run TTS: job has no script_text."
            )

        tts_service = get_tts_service(provider)
        result = await tts_service.synthesize(
            text=script_text,
            voice_id=voice_id,
            output_path=ctx.voice_path,
        )
        logger.info(
            "[%s] TTS done: %.1fs audio, %d chars",
            ctx.job_id,
            result.duration_sec,
            result.char_count,
        )

    async def _step_fetch_images(self, job, ctx: PipelineContext) -> None:
        """Fetch stock images for the video background."""
        logger.info("[%s] Step 2/5: Fetching images", ctx.job_id)

        from app.services.assets import fetch_images

        keywords: list[str] = getattr(job, "keywords", None) or ["horror", "dark", "atmospheric"]
        image_count = 5

        paths = await fetch_images(
            keywords=keywords,
            count=image_count,
            output_dir=ctx.tmp_dir,
            pexels_key=self.settings.PEXELS_API_KEY,
            pixabay_key=self.settings.PIXABAY_API_KEY,
        )

        if not paths:
            raise VideoProcessingError(
                f"[{ctx.job_id}] No images could be fetched for keywords: {keywords}"
            )

        ctx.image_paths = paths
        logger.info("[%s] Fetched %d images", ctx.job_id, len(paths))

    async def _step_captions(self, ctx: PipelineContext) -> None:
        """Transcribe voice audio to SRT captions."""
        logger.info("[%s] Step 3/5: Generating captions", ctx.job_id)

        # Run synchronous Whisper in a thread to avoid blocking the event loop
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            self.whisper.transcribe_to_srt,
            ctx.voice_path,
            ctx.srt_path,
        )
        logger.info("[%s] Captions written to %s", ctx.job_id, ctx.srt_path)

    async def _step_assemble(self, job, ctx: PipelineContext) -> None:
        """Build the video: resize images → ken-burns clips → concat → audio mix → captions."""
        logger.info("[%s] Step 4/5: Assembling video", ctx.job_id)

        voice_duration = self.ffmpeg.get_duration(ctx.voice_path)
        clip_duration = max(3.0, voice_duration / max(len(ctx.image_paths), 1))

        loop = asyncio.get_running_loop()

        # --- Resize images and apply Ken Burns ---
        clip_paths: list[str] = []
        for i, img_path in enumerate(ctx.image_paths):
            resized = os.path.join(ctx.tmp_dir, f"resized_{i}.jpg")
            clip_out = os.path.join(ctx.tmp_dir, f"clip_{i}.mp4")

            await loop.run_in_executor(
                None, self.ffmpeg.resize_image, img_path, resized
            )
            await loop.run_in_executor(
                None,
                lambda r=resized, c=clip_out, d=clip_duration: self.ffmpeg.ken_burns(
                    r, c, duration=d, zoom_start=1.0, zoom_end=1.05
                ),
            )
            clip_paths.append(clip_out)

        ctx.clip_paths = clip_paths
        ctx.concat_path = os.path.join(ctx.tmp_dir, "concat.mp4")
        ctx.mixed_path = os.path.join(ctx.tmp_dir, "mixed.mp4")
        captioned_path = os.path.join(ctx.tmp_dir, "captioned.mp4")

        # --- Concatenate clips ---
        await loop.run_in_executor(
            None,
            lambda: self.ffmpeg.concat_clips(
                ctx.clip_paths, ctx.concat_path, crossfade_sec=0.5
            ),
        )

        # --- Mix audio ---
        music_path: str | None = ctx.music_path if ctx.music_path else None
        await loop.run_in_executor(
            None,
            lambda: self.ffmpeg.add_audio_mix(
                ctx.concat_path,
                ctx.voice_path,
                music_path,
                ctx.mixed_path,
                music_volume=0.15,
            ),
        )

        # --- Burn captions ---
        if os.path.isfile(ctx.srt_path) and os.path.getsize(ctx.srt_path) > 0:
            await loop.run_in_executor(
                None,
                lambda: self.ffmpeg.burn_captions(
                    ctx.mixed_path, ctx.srt_path, captioned_path
                ),
            )
            # Point mixed_path to the captioned version for the next step
            ctx.mixed_path = captioned_path
        else:
            logger.warning("[%s] No captions file — skipping burn step.", ctx.job_id)

        logger.info("[%s] Assembly complete", ctx.job_id)

    async def _step_move_to_media(self, ctx: PipelineContext) -> None:
        """Move the final video to the media/previews directory."""
        logger.info("[%s] Step 5/5: Moving to media store", ctx.job_id)

        dest_dir = os.path.join(self.settings.MEDIA_DIR, "previews")
        os.makedirs(dest_dir, exist_ok=True)

        ctx.final_path = os.path.join(dest_dir, f"{ctx.job_id}.mp4")

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            shutil.copy2,
            ctx.mixed_path,
            ctx.final_path,
        )
        logger.info("[%s] Final video at %s", ctx.job_id, ctx.final_path)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _cleanup_tmp(self, ctx: PipelineContext) -> None:
        """Remove the temporary working directory."""
        try:
            shutil.rmtree(ctx.tmp_dir, ignore_errors=True)
            logger.debug("[%s] Cleaned up tmp dir %s", ctx.job_id, ctx.tmp_dir)
        except Exception:
            logger.warning(
                "[%s] Could not clean up tmp dir %s", ctx.job_id, ctx.tmp_dir
            )

    def _make_context(self, job) -> PipelineContext:
        """Build a PipelineContext from a VideoJob."""
        job_id = str(getattr(job, "id", uuid.uuid4()))
        tmp_dir = os.path.join("/tmp", job_id)

        music_category = getattr(job, "music_category", None) or "horror_ambient"
        music_path = self._pick_music(music_category) or ""

        return PipelineContext(
            job_id=job_id,
            tmp_dir=tmp_dir,
            voice_path=os.path.join(tmp_dir, "voice.mp3"),
            srt_path=os.path.join(tmp_dir, "captions.srt"),
            music_path=music_path,
        )

    def _pick_music(self, category: str) -> str | None:
        """Return a random music track from the assets library for the given category."""
        from app.services.assets import MusicLibrary

        library = MusicLibrary(self.settings.ASSETS_DIR)
        return library.get_track(category)
