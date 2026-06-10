from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from faster_whisper import WhisperModel


class WhisperService:
    """Transcription service powered by faster-whisper.

    The model is loaded lazily on first use to avoid slow startup times.
    """

    def __init__(self, model_size: str = "base") -> None:
        self._model: "WhisperModel | None" = None
        self.model_size = model_size

    def _get_model(self) -> "WhisperModel":
        if self._model is None:
            from faster_whisper import WhisperModel

            logger.info("Loading Whisper model '%s' (CPU int8)…", self.model_size)
            self._model = WhisperModel(
                self.model_size,
                device="cpu",
                compute_type="int8",
            )
            logger.info("Whisper model loaded.")
        return self._model

    def transcribe_to_srt(self, audio_path: str, output_srt_path: str) -> str:
        """Transcribe an audio file to an SRT subtitle file.

        Uses word-level timestamps and groups words into ~4-word chunks of
        approximately 0.5 s each for comfortable reading pace.

        Returns the SRT content as a string (also writes it to output_srt_path).
        """
        model = self._get_model()

        logger.info("Transcribing %s …", audio_path)
        segments, _ = model.transcribe(
            audio_path,
            word_timestamps=True,
        )

        # Collect all words with their start/end times
        words: list[tuple[float, float, str]] = []
        for segment in segments:
            if segment.words:
                for word in segment.words:
                    words.append((word.start, word.end, word.word.strip()))

        if not words:
            logger.warning("Whisper produced no words for %s", audio_path)
            srt_content = ""
            with open(output_srt_path, "w", encoding="utf-8") as f:
                f.write(srt_content)
            return srt_content

        # Group words into chunks of ~4 words (or shorter if a long gap appears)
        chunks: list[tuple[float, float, str]] = []
        chunk_size = 4
        i = 0
        while i < len(words):
            group = words[i : i + chunk_size]
            start = group[0][0]
            end = group[-1][1]
            text = " ".join(w[2] for w in group if w[2])
            if text:
                chunks.append((start, end, text))
            i += chunk_size

        # Build SRT content
        srt_lines: list[str] = []
        for idx, (start, end, text) in enumerate(chunks, start=1):
            srt_lines.append(str(idx))
            srt_lines.append(
                f"{self._format_timestamp(start)} --> {self._format_timestamp(end)}"
            )
            srt_lines.append(text)
            srt_lines.append("")  # blank line between entries

        srt_content = "\n".join(srt_lines)

        os.makedirs(os.path.dirname(os.path.abspath(output_srt_path)), exist_ok=True)
        with open(output_srt_path, "w", encoding="utf-8") as f:
            f.write(srt_content)

        logger.info("SRT written to %s (%d chunks)", output_srt_path, len(chunks))
        return srt_content

    def _format_timestamp(self, seconds: float) -> str:
        """Convert seconds to SRT timestamp format: HH:MM:SS,mmm."""
        total_ms = int(round(seconds * 1000))
        ms = total_ms % 1000
        total_s = total_ms // 1000
        s = total_s % 60
        total_m = total_s // 60
        m = total_m % 60
        h = total_m // 60
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
