from __future__ import annotations

import json
import logging
import os
import subprocess
from typing import Any

logger = logging.getLogger(__name__)


class VideoProcessingError(Exception):
    """Raised when an ffmpeg / ffprobe command exits with a non-zero status."""


class FFmpegUtils:
    """Thin wrapper around ffmpeg and ffprobe for video processing operations.

    All output is 9:16 vertical (1080x1920) by default. Operations raise
    VideoProcessingError on hard failure; callers decide what is fatal.
    """

    WIDTH = 1080
    HEIGHT = 1920
    FPS = 30

    def __init__(
        self,
        ffmpeg_path: str = "/usr/bin/ffmpeg",
        ffprobe_path: str | None = None,
    ) -> None:
        self.ffmpeg = ffmpeg_path
        if ffprobe_path and os.path.isfile(ffprobe_path):
            self.ffprobe = ffprobe_path
        else:
            sibling = os.path.join(os.path.dirname(ffmpeg_path), "ffprobe")
            self.ffprobe = sibling if os.path.isfile(sibling) else "ffprobe"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _run(self, args: list[str], timeout: int = 300) -> subprocess.CompletedProcess:
        """Run a command, raise VideoProcessingError on non-zero exit."""
        logger.debug("FFmpegUtils running: %s", " ".join(args))
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode != 0:
            raise VideoProcessingError(
                f"Command failed (exit {result.returncode}):\n"
                f"CMD : {' '.join(args)}\n"
                f"STDERR: {result.stderr[-2000:]}"
            )
        return result

    # ------------------------------------------------------------------
    # Image / clip building
    # ------------------------------------------------------------------

    def resize_image(
        self,
        src: str,
        dst: str,
        width: int = WIDTH,
        height: int = HEIGHT,
    ) -> None:
        """Resize/centre-crop an image to 9:16 vertical. Produces a JPEG at dst."""
        filter_chain = (
            f"scale={width}:{height}:force_original_aspect_ratio=increase,"
            f"crop={width}:{height}"
        )
        self._run([
            self.ffmpeg, "-y",
            "-i", src,
            "-vf", filter_chain,
            "-q:v", "2",
            dst,
        ])

    def ken_burns(
        self,
        image_path: str,
        output_path: str,
        duration: float = 5.0,
        zoom_start: float = 1.0,
        zoom_end: float = 1.08,
    ) -> None:
        """Apply a slow Ken Burns zoom to a static image → silent 1080x1920 clip.

        The image is assumed already at 1080x1920. Min 1s duration enforced.
        """
        duration = max(1.0, float(duration))
        total_frames = max(1, int(duration * self.FPS))
        zoom_range = zoom_end - zoom_start
        zoom_expr = f"{zoom_start}+{zoom_range}*on/{total_frames}"
        zoompan_filter = (
            f"zoompan="
            f"z='{zoom_expr}':"
            f"x='iw/2-(iw/zoom/2)':"
            f"y='ih/2-(ih/zoom/2)':"
            f"d={total_frames}:"
            f"s={self.WIDTH}x{self.HEIGHT}:"
            f"fps={self.FPS}"
        )
        self._run([
            self.ffmpeg, "-y",
            "-loop", "1",
            "-i", image_path,
            "-vf", zoompan_filter,
            "-t", f"{duration:.3f}",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "fast",
            output_path,
        ], timeout=180)

    def loop_footage(
        self,
        src: str,
        output_path: str,
        duration: float,
    ) -> None:
        """Loop/trim a footage clip to exactly ``duration`` at 1080x1920, silent."""
        duration = max(1.0, float(duration))
        vf = (
            f"scale={self.WIDTH}:{self.HEIGHT}:force_original_aspect_ratio=increase,"
            f"crop={self.WIDTH}:{self.HEIGHT},fps={self.FPS}"
        )
        self._run([
            self.ffmpeg, "-y",
            "-stream_loop", "-1",
            "-i", src,
            "-t", f"{duration:.3f}",
            "-vf", vf,
            "-an",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "fast",
            output_path,
        ], timeout=300)

    def concat_clips(self, clip_paths: list[str], output_path: str) -> None:
        """Concatenate silent 1080x1920 clips end-to-end (no transitions)."""
        if not clip_paths:
            raise VideoProcessingError("concat_clips: no clip paths provided.")
        if len(clip_paths) == 1:
            self._run([self.ffmpeg, "-y", "-i", clip_paths[0], "-c", "copy", output_path])
            return

        input_args: list[str] = []
        for p in clip_paths:
            input_args += ["-i", p]
        n = len(clip_paths)
        streams = "".join(f"[{i}:v:0]" for i in range(n))
        filter_complex = f"{streams}concat=n={n}:v=1:a=0[outv]"
        cmd = (
            [self.ffmpeg, "-y"]
            + input_args
            + [
                "-filter_complex", filter_complex,
                "-map", "[outv]",
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-preset", "fast",
                output_path,
            ]
        )
        self._run(cmd, timeout=600)

    # ------------------------------------------------------------------
    # Audio mixing (ducked music under narration)
    # ------------------------------------------------------------------

    def mix_audio(
        self,
        video_path: str,
        voice_path: str,
        music_path: str | None,
        output_path: str,
        music_volume: float = 0.12,
    ) -> None:
        """Mux narration (full) + optional ducked music onto a silent video.

        Music is sidechain-compressed (ducked) under the narration so the voice
        stays clear. Output MP4 length matches the narration (shortest).
        """
        if music_path and os.path.isfile(music_path):
            filter_complex = (
                "[1:a]aformat=sample_rates=44100:channel_layouts=stereo[voice];"
                "[2:a]aformat=sample_rates=44100:channel_layouts=stereo,"
                f"volume={music_volume}[bg];"
                "[bg][voice]sidechaincompress=threshold=0.02:ratio=12:"
                "attack=20:release=400[ducked];"
                "[voice][ducked]amix=inputs=2:duration=first:"
                "dropout_transition=2[aout]"
            )
            self._run([
                self.ffmpeg, "-y",
                "-i", video_path,
                "-i", voice_path,
                "-i", music_path,
                "-filter_complex", filter_complex,
                "-map", "0:v",
                "-map", "[aout]",
                "-c:v", "copy",
                "-c:a", "aac",
                "-b:a", "192k",
                "-shortest",
                output_path,
            ], timeout=300)
        else:
            self._run([
                self.ffmpeg, "-y",
                "-i", video_path,
                "-i", voice_path,
                "-map", "0:v",
                "-map", "1:a",
                "-c:v", "copy",
                "-c:a", "aac",
                "-b:a", "192k",
                "-shortest",
                output_path,
            ], timeout=300)

    # ------------------------------------------------------------------
    # Captions
    # ------------------------------------------------------------------

    def burn_subtitles(
        self,
        video_path: str,
        ass_path: str,
        output_path: str,
    ) -> None:
        """Burn an ASS subtitle file (word-by-word captions) into the video."""
        subtitle_filter = f"ass={_escape_path(ass_path)}"
        self._run([
            self.ffmpeg, "-y",
            "-i", video_path,
            "-vf", subtitle_filter,
            "-c:v", "libx264",
            "-crf", "18",
            "-preset", "fast",
            "-c:a", "copy",
            output_path,
        ], timeout=300)

    # ------------------------------------------------------------------
    # Probing
    # ------------------------------------------------------------------

    def get_duration(self, media_path: str) -> float:
        """Return media duration in seconds using ffprobe."""
        result = self._run([
            self.ffprobe,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            media_path,
        ])
        try:
            info = json.loads(result.stdout)
            return float(info["format"]["duration"])
        except (json.JSONDecodeError, KeyError, ValueError) as exc:
            raise VideoProcessingError(
                f"Could not parse ffprobe duration output for {media_path}: {exc}"
            ) from exc

    def get_video_info(self, path: str) -> dict[str, Any]:
        """Return {width, height, duration, fps} using ffprobe JSON."""
        result = self._run([
            self.ffprobe,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            path,
        ])
        try:
            info = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise VideoProcessingError(
                f"Could not parse ffprobe output for {path}: {exc}"
            ) from exc

        video_stream: dict = {}
        for stream in info.get("streams", []):
            if stream.get("codec_type") == "video":
                video_stream = stream
                break

        duration = float(info.get("format", {}).get("duration", 0))
        width = int(video_stream.get("width", 0))
        height = int(video_stream.get("height", 0))

        fps = 0.0
        avg_frame_rate = video_stream.get("avg_frame_rate", "0/1")
        try:
            num, den = avg_frame_rate.split("/")
            if float(den) != 0:
                fps = float(num) / float(den)
        except (ValueError, ZeroDivisionError):
            fps = 0.0

        return {"width": width, "height": height, "duration": duration, "fps": fps}


def _escape_path(path: str) -> str:
    """Escape a file path for use inside an ffmpeg filter string."""
    return path.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")
