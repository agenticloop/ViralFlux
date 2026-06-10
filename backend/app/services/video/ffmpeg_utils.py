from __future__ import annotations

import json
import logging
import os
import subprocess
import tempfile
from typing import Any

logger = logging.getLogger(__name__)


class VideoProcessingError(Exception):
    """Raised when an ffmpeg / ffprobe command exits with a non-zero status."""


class FFmpegUtils:
    """Thin wrapper around ffmpeg and ffprobe for video processing operations."""

    def __init__(self, ffmpeg_path: str = "/usr/bin/ffmpeg") -> None:
        self.ffmpeg = ffmpeg_path
        self.ffprobe = os.path.join(os.path.dirname(ffmpeg_path), "ffprobe")
        # Fall back to system PATH if sibling not found
        if not os.path.isfile(self.ffprobe):
            self.ffprobe = "ffprobe"

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
    # Public API
    # ------------------------------------------------------------------

    def resize_image(
        self,
        src: str,
        dst: str,
        width: int = 1080,
        height: int = 1920,
    ) -> None:
        """Resize an image to the target dimensions (9:16 vertical) using
        scale-then-pad to letterbox, or crop if the source is wider.

        Produces a JPEG at dst.
        """
        # scale to fill the height, pad sides; then centre-crop to exact size
        filter_chain = (
            f"scale={width}:{height}:force_original_aspect_ratio=increase,"
            f"crop={width}:{height}"
        )
        self._run([
            self.ffmpeg,
            "-y",
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
        zoom_end: float = 1.05,
    ) -> None:
        """Apply a slow Ken Burns zoom effect to a static image, producing a
        short video clip of the given duration at 30 fps.

        The image is assumed to already be at 1080x1920. The zoompan filter
        interpolates zoom from zoom_start to zoom_end over the clip duration.
        """
        fps = 30
        total_frames = int(duration * fps)
        zoom_range = zoom_end - zoom_start

        # zoompan formula: zoom progresses linearly from zoom_start to zoom_end
        zoom_expr = f"{zoom_start}+{zoom_range}*on/{total_frames}"
        zoompan_filter = (
            f"zoompan="
            f"z='{zoom_expr}':"
            f"x='iw/2-(iw/zoom/2)':"
            f"y='ih/2-(ih/zoom/2)':"
            f"d={total_frames}:"
            f"s=1080x1920:"
            f"fps={fps}"
        )

        self._run([
            self.ffmpeg,
            "-y",
            "-loop", "1",
            "-i", image_path,
            "-vf", zoompan_filter,
            "-t", str(duration),
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-preset", "fast",
            output_path,
        ], timeout=120)

    def concat_clips(
        self,
        clip_paths: list[str],
        output_path: str,
        crossfade_sec: float = 0.5,
    ) -> None:
        """Concatenate video clips with xfade crossfade transitions between them.

        Each clip is assumed to be at 1080x1920 30 fps with no audio.
        """
        if not clip_paths:
            raise VideoProcessingError("concat_clips: no clip paths provided.")

        if len(clip_paths) == 1:
            # Nothing to concatenate — just copy
            self._run([self.ffmpeg, "-y", "-i", clip_paths[0], "-c", "copy", output_path])
            return

        # Build a filtergraph that chains xfade between all clips.
        # Each clip's duration is needed to set the offset correctly.
        durations = [self.get_duration(p) for p in clip_paths]

        input_args: list[str] = []
        for p in clip_paths:
            input_args += ["-i", p]

        # Build the xfade filter chain
        filter_parts: list[str] = []
        prev_label = "[0:v]"
        cumulative_duration = durations[0]

        for i in range(1, len(clip_paths)):
            offset = max(0.0, cumulative_duration - crossfade_sec)
            out_label = f"[xf{i}]" if i < len(clip_paths) - 1 else "[outv]"
            filter_parts.append(
                f"{prev_label}[{i}:v]xfade=transition=fade:"
                f"duration={crossfade_sec}:offset={offset:.3f}{out_label}"
            )
            prev_label = out_label
            cumulative_duration += durations[i] - crossfade_sec

        filter_complex = ";".join(filter_parts)

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
        self._run(cmd, timeout=300)

    def add_audio_mix(
        self,
        video_path: str,
        voice_path: str,
        music_path: str | None,
        output_path: str,
        music_volume: float = 0.15,
    ) -> None:
        """Mix narration voice (full volume) and optional background music
        (attenuated to music_volume) onto a muted video track.

        Output is an MP4 with AAC audio.
        """
        if music_path and os.path.isfile(music_path):
            # Mix voice + music: voice at 1.0, music at music_volume
            filter_complex = (
                f"[1:a]aformat=sample_rates=44100:channel_layouts=stereo[voice];"
                f"[2:a]aformat=sample_rates=44100:channel_layouts=stereo,"
                f"volume={music_volume}[music];"
                f"[voice][music]amix=inputs=2:duration=first:dropout_transition=2[aout]"
            )
            self._run([
                self.ffmpeg,
                "-y",
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
            # Voice only — no music
            self._run([
                self.ffmpeg,
                "-y",
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

    def burn_captions(
        self,
        video_path: str,
        srt_path: str,
        output_path: str,
    ) -> None:
        """Burn SRT subtitles onto the video.

        Style: white Arial Bold 48pt with black outline, positioned in the
        bottom 25% of the frame (Alignment=2 = bottom-centre in ASS/SSA).
        """
        # Use the subtitles filter — it natively reads .srt files.
        # Force style overrides for readability.
        subtitle_filter = (
            f"subtitles={_escape_path(srt_path)}"
            f":force_style='FontName=Arial,Bold=1,FontSize=48,"
            f"PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
            f"Outline=3,Shadow=1,Alignment=2,MarginV=60'"
        )

        self._run([
            self.ffmpeg,
            "-y",
            "-i", video_path,
            "-vf", subtitle_filter,
            "-c:v", "libx264",
            "-crf", "18",
            "-preset", "fast",
            "-c:a", "copy",
            output_path,
        ], timeout=300)

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
        """Return a dict with {width, height, duration, fps} using ffprobe JSON."""
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

        # Find the first video stream
        video_stream: dict = {}
        for stream in info.get("streams", []):
            if stream.get("codec_type") == "video":
                video_stream = stream
                break

        duration = float(info.get("format", {}).get("duration", 0))
        width = int(video_stream.get("width", 0))
        height = int(video_stream.get("height", 0))

        # Parse fps from avg_frame_rate e.g. "30000/1001" or "30/1"
        fps = 0.0
        avg_frame_rate = video_stream.get("avg_frame_rate", "0/1")
        try:
            num, den = avg_frame_rate.split("/")
            if float(den) != 0:
                fps = float(num) / float(den)
        except (ValueError, ZeroDivisionError):
            fps = 0.0

        return {
            "width": width,
            "height": height,
            "duration": duration,
            "fps": fps,
        }


def _escape_path(path: str) -> str:
    """Escape a file path for use inside an ffmpeg filter string."""
    # Escape backslashes, colons, and single quotes
    return path.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")


def _build_concat_filtergraph(
    n: int,
    crossfade_sec: float,
    durations: list[float],
) -> str:
    """Build an xfade filter chain for n clips."""
    if n == 1:
        return "[0:v][outv]copy"

    parts: list[str] = []
    prev_label = "[0:v]"
    cumulative = durations[0]

    for i in range(1, n):
        offset = max(0.0, cumulative - crossfade_sec)
        out_label = f"[xf{i}]" if i < n - 1 else "[outv]"
        parts.append(
            f"{prev_label}[{i}:v]xfade=transition=fade:"
            f"duration={crossfade_sec}:offset={offset:.3f}{out_label}"
        )
        prev_label = out_label
        cumulative += durations[i] - crossfade_sec

    return ";".join(parts)
