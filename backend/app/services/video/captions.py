"""Burned-in word-by-word caption builder for ViralFlux.

Produces ASS (Advanced SubStation Alpha) subtitle files that ffmpeg can burn
into a video. Captions are word-by-word: at any moment the *current* word is
highlighted while its short context line stays visible.

Two presets:

* ``brainrot`` — bold, large (~130px), heavy black stroke, yellow base text with
  a red highlight on the current word, bottom-centred. Loud and energetic.
* ``horror``   — cleaner and smaller, white text, slower fade, lower visual
  weight so it doesn't fight the atmosphere.

Word timestamps are a list of ``{"word", "start", "end"}`` dicts (seconds).
Primary source is ElevenLabs character/word timestamps; :func:`build_ass_from_whisper`
is a dependency-light fallback using faster-whisper.

ASS text is written directly — no moviepy / libass-python dependency.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class _CaptionStyle:
    """Resolved visual parameters for a caption preset.

    Colours are ASS ``&HAABBGGRR`` (alpha, blue, green, red — note BGR order).
    """

    font: str
    fontsize: int
    base_colour: str        # PrimaryColour (resting word colour)
    highlight_colour: str   # current-word colour
    outline_colour: str     # BackColour / OutlineColour
    outline: int            # stroke thickness in px
    shadow: int
    bold: int               # -1 = bold, 0 = normal (ASS convention)
    margin_v: int           # vertical margin from bottom
    fade_ms: int            # per-line fade in/out
    words_per_line: int     # context words shown around the active word


# ASS colour helper note: format is &H<AA><BB><GG><RR>
_STYLES: dict[str, _CaptionStyle] = {
    "brainrot": _CaptionStyle(
        font="Arial Black",
        fontsize=130,
        base_colour="&H0000FFFF",       # opaque yellow (R=FF,G=FF,B=00)
        highlight_colour="&H000000FF",  # opaque red   (R=FF,G=00,B=00)
        outline_colour="&H00000000",    # opaque black
        outline=8,
        shadow=2,
        bold=-1,
        margin_v=260,
        fade_ms=60,
        words_per_line=3,
    ),
    "horror": _CaptionStyle(
        font="Arial",
        fontsize=84,
        base_colour="&H00FFFFFF",       # opaque white
        highlight_colour="&H00DDDDDD",  # soft grey emphasis (subtle)
        outline_colour="&H00000000",    # opaque black
        outline=3,
        shadow=1,
        bold=-1,
        margin_v=320,
        fade_ms=350,
        words_per_line=4,
    ),
}


def _resolve_style(style: str) -> _CaptionStyle:
    return _STYLES.get(style, _STYLES["horror"])


def _format_ts(seconds: float) -> str:
    """Format seconds as an ASS timestamp ``H:MM:SS.cc`` (centiseconds)."""
    if seconds < 0:
        seconds = 0.0
    total_cs = int(round(seconds * 100))
    cs = total_cs % 100
    total_s = total_cs // 100
    s = total_s % 60
    total_m = total_s // 60
    m = total_m % 60
    h = total_m // 60
    return f"{h:d}:{m:02d}:{s:02d}.{cs:02d}"


def _escape(text: str) -> str:
    """Escape characters that have meaning in ASS dialogue text."""
    # Curly braces start override blocks; a literal newline would break the line.
    return text.replace("{", "(").replace("}", ")").replace("\n", " ").strip()


def _build_header(st: _CaptionStyle, video_w: int, video_h: int) -> str:
    """Build the ``[Script Info]`` + ``[V4+ Styles]`` header for ``st``."""
    return (
        "[Script Info]\n"
        "ScriptType: v4.00+\n"
        "WrapStyle: 2\n"
        "ScaledBorderAndShadow: yes\n"
        f"PlayResX: {video_w}\n"
        f"PlayResY: {video_h}\n"
        "\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
        "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, "
        "ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, "
        "MarginL, MarginR, MarginV, Encoding\n"
        f"Style: Caption,{st.font},{st.fontsize},{st.base_colour},"
        f"{st.highlight_colour},{st.outline_colour},{st.outline_colour},"
        f"{st.bold},0,0,0,100,100,0,0,1,{st.outline},{st.shadow},2,40,40,"
        f"{st.margin_v},1\n"
        "\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, "
        "Effect, Text\n"
    )


def _line_groups(
    word_timestamps: list[dict], words_per_line: int
) -> list[list[dict]]:
    """Chunk words into fixed-size context lines, preserving order."""
    groups: list[list[dict]] = []
    for i in range(0, len(word_timestamps), words_per_line):
        groups.append(word_timestamps[i : i + words_per_line])
    return groups


def _render_word(text: str, st: _CaptionStyle, *, active: bool) -> str:
    """Render a single word with the right colour for active/resting state."""
    safe = _escape(text)
    if active:
        return f"{{\\c{st.highlight_colour}}}{safe}{{\\c{st.base_colour}}}"
    return safe


def build_ass(
    word_timestamps: list[dict],
    style: str,
    out_path: str,
    video_w: int = 1080,
    video_h: int = 1920,
) -> str:
    """Build a word-by-word highlighted ASS subtitle file.

    Words are grouped into short context lines (preset-dependent). For each word,
    one Dialogue event is emitted spanning that word's ``[start, end]`` with the
    active word highlighted and its line-mates shown in the resting colour. This
    yields a karaoke-style "current word lights up" effect across the line.

    Args:
        word_timestamps: ``[{"word", "start", "end"}, ...]`` in seconds, ordered.
        style: ``"brainrot"`` or ``"horror"`` (unknown values fall back to horror).
        out_path: Destination ``.ass`` path.
        video_w: Render width (PlayResX), default 1080.
        video_h: Render height (PlayResY), default 1920.

    Returns:
        The ASS document as a string (also written to ``out_path``).
    """
    st = _resolve_style(style)
    lines: list[str] = [_build_header(st, video_w, video_h)]

    groups = _line_groups(word_timestamps, st.words_per_line)
    for group in groups:
        for active_idx, active_word in enumerate(group):
            start = float(active_word.get("start", 0.0))
            end = float(active_word.get("end", start))
            if end <= start:
                # Guarantee a visible minimum so very short words still render.
                end = start + 0.08

            rendered = " ".join(
                _render_word(w.get("word", ""), st, active=(j == active_idx))
                for j, w in enumerate(group)
            )
            fade = f"{{\\fad({st.fade_ms},{st.fade_ms})}}"
            text = f"{fade}{rendered}"
            lines.append(
                f"Dialogue: 0,{_format_ts(start)},{_format_ts(end)},Caption,,"
                f"0,0,0,,{text}"
            )

    ass_doc = "\n".join(lines) + "\n"

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(ass_doc)

    logger.info(
        "Wrote ASS captions (%s preset, %d words) to %s",
        style,
        len(word_timestamps),
        out_path,
    )
    return ass_doc


def build_ass_from_whisper(audio_path: str, style: str, out_path: str) -> str:
    """Fallback: build captions from faster-whisper word timestamps.

    Used when ElevenLabs word timestamps are unavailable. faster-whisper is
    imported lazily so the module loads without it; a clear ``RuntimeError`` is
    raised if it is missing.

    Args:
        audio_path: Path to the narration audio to transcribe.
        style: Caption preset (see :func:`build_ass`).
        out_path: Destination ``.ass`` path.

    Returns:
        The ASS document as a string.
    """
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError(
            "faster-whisper is not installed; cannot build captions from audio. "
            "Install faster-whisper or supply ElevenLabs word timestamps."
        ) from exc

    from app.core.config import settings

    logger.info(
        "Transcribing %s with faster-whisper (model=%s) for caption fallback",
        audio_path,
        settings.WHISPER_MODEL,
    )
    model = WhisperModel(settings.WHISPER_MODEL, device="cpu", compute_type="int8")
    segments, _ = model.transcribe(audio_path, word_timestamps=True)

    word_timestamps: list[dict] = []
    for segment in segments:
        for word in segment.words or []:
            text = word.word.strip()
            if not text:
                continue
            word_timestamps.append(
                {"word": text, "start": float(word.start), "end": float(word.end)}
            )

    if not word_timestamps:
        logger.warning("faster-whisper produced no words for %s", audio_path)

    # Resolution from settings (e.g. "1080x1920").
    try:
        w_str, h_str = settings.VIDEO_RESOLUTION.lower().split("x")
        video_w, video_h = int(w_str), int(h_str)
    except (ValueError, AttributeError):
        video_w, video_h = 1080, 1920

    return build_ass(word_timestamps, style, out_path, video_w, video_h)
