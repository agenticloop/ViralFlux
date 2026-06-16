from __future__ import annotations

import asyncio
import base64
import logging
from typing import Any

import httpx

from app.core.config import settings
from app.core.pricing import tts_cost_usd

from .base import TTSResult, TTSService

logger = logging.getLogger(__name__)

# Network tuning -------------------------------------------------------------
_CONNECT_TIMEOUT = 10.0
_READ_TIMEOUT = 120.0          # generation can take a while for long scripts
_TIMEOUT = httpx.Timeout(_READ_TIMEOUT, connect=_CONNECT_TIMEOUT)
_MAX_RETRIES = 3               # total attempts on transient failures
_BACKOFF_BASE = 0.75           # seconds; exponential

# Output format for the binary endpoints; mp3 44.1kHz 128kbps.
_OUTPUT_FORMAT = "mp3_44100_128"

# HTTP status codes worth retrying (transient server / rate-limit errors).
_RETRYABLE_STATUS = frozenset({429, 500, 502, 503, 504})


class ElevenLabsError(RuntimeError):
    """Raised when an ElevenLabs operation fails or cannot be attempted."""


class ElevenLabsService(TTSService):
    """ElevenLabs TTS provider backed by the raw REST API via httpx.

    The service is tolerant of a missing API key: it constructs cleanly so the
    app can boot with placeholder config, and raises a clear ``ElevenLabsError``
    (a ``RuntimeError``) only when a key-requiring operation is actually called.
    """

    provider = "elevenlabs"

    def __init__(self) -> None:
        self._base_url = settings.ELEVENLABS_BASE_URL.rstrip("/")
        self._model_id = settings.ELEVENLABS_MODEL

    # -- internals ----------------------------------------------------------
    @property
    def _api_key(self) -> str:
        return settings.ELEVENLABS_API_KEY or ""

    def _require_key(self) -> str:
        key = self._api_key
        if not key:
            raise ElevenLabsError(
                "ELEVENLABS_API_KEY is not set. ElevenLabs is the only TTS "
                "provider; set ELEVENLABS_API_KEY to synthesize audio."
            )
        return key

    def _headers(self, *, json_accept: bool = True) -> dict[str, str]:
        headers = {"xi-api-key": self._require_key()}
        if json_accept:
            headers["Accept"] = "application/json"
        return headers

    async def _request(
        self,
        method: str,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> httpx.Response:
        """Issue a request with retry/backoff on transient failures."""
        url = f"{self._base_url}{path}"
        last_exc: Exception | None = None

        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                    resp = await client.request(
                        method, url, headers=headers, params=params, json=json
                    )
                if resp.status_code in _RETRYABLE_STATUS:
                    raise httpx.HTTPStatusError(
                        f"retryable status {resp.status_code}",
                        request=resp.request,
                        response=resp,
                    )
                return resp
            except (httpx.TransportError, httpx.HTTPStatusError) as exc:
                last_exc = exc
                if attempt >= _MAX_RETRIES:
                    break
                delay = _BACKOFF_BASE * (2 ** (attempt - 1))
                logger.warning(
                    "ElevenLabs %s %s failed (attempt %d/%d): %s; retrying in %.2fs",
                    method, path, attempt, _MAX_RETRIES, exc, delay,
                )
                await asyncio.sleep(delay)

        raise ElevenLabsError(
            f"ElevenLabs request {method} {path} failed after "
            f"{_MAX_RETRIES} attempts: {last_exc}"
        ) from last_exc

    # -- synthesis ----------------------------------------------------------
    async def synthesize(
        self,
        text: str,
        voice_id: str,
        voice_settings: dict,
        out_path: str,
    ) -> TTSResult:
        """Synthesize ``text`` and write an MP3 to ``out_path``.

        Uses the ``/with-timestamps`` endpoint to obtain character-level
        alignment, which we collapse to word-level timestamps. If that endpoint
        is unavailable (404/405), falls back to the plain text-to-speech
        endpoint with no timestamps.
        """
        text = (text or "").strip()
        if not text:
            raise ElevenLabsError("Cannot synthesize empty text.")
        if not voice_id:
            raise ElevenLabsError("A voice_id is required for synthesis.")

        self._require_key()
        char_count = len(text)
        cost = tts_cost_usd(text)

        body: dict[str, Any] = {
            "text": text,
            "model_id": self._model_id,
        }
        if voice_settings:
            body["voice_settings"] = voice_settings

        params = {"output_format": _OUTPUT_FORMAT}

        # Primary: with-timestamps (returns JSON: base64 audio + alignment).
        resp = await self._request(
            "POST",
            f"/v1/text-to-speech/{voice_id}/with-timestamps",
            headers=self._headers(json_accept=True),
            params=params,
            json=body,
        )

        if resp.status_code in (404, 405):
            logger.info(
                "with-timestamps unavailable (%d); falling back to plain TTS.",
                resp.status_code,
            )
            return await self._synthesize_plain(
                voice_id, body, params, out_path, char_count, cost
            )

        if resp.status_code >= 400:
            raise ElevenLabsError(
                f"ElevenLabs synthesis failed ({resp.status_code}): "
                f"{_safe_text(resp)}"
            )

        payload = resp.json()
        audio_b64 = payload.get("audio_base64") or payload.get("audio")
        if not audio_b64:
            raise ElevenLabsError("ElevenLabs response missing audio data.")

        _write_bytes(out_path, base64.b64decode(audio_b64))

        alignment = (
            payload.get("alignment")
            or payload.get("normalized_alignment")
            or {}
        )
        word_timestamps = _chars_to_words(alignment)

        return TTSResult(
            audio_path=out_path,
            char_count=char_count,
            cost_usd=cost,
            word_timestamps=word_timestamps,
        )

    async def _synthesize_plain(
        self,
        voice_id: str,
        body: dict[str, Any],
        params: dict[str, Any],
        out_path: str,
        char_count: int,
        cost: float,
    ) -> TTSResult:
        """Plain text-to-speech (binary MP3 stream, no timestamps)."""
        resp = await self._request(
            "POST",
            f"/v1/text-to-speech/{voice_id}",
            headers={"xi-api-key": self._require_key(), "Accept": "audio/mpeg"},
            params=params,
            json=body,
        )
        if resp.status_code >= 400:
            raise ElevenLabsError(
                f"ElevenLabs synthesis failed ({resp.status_code}): "
                f"{_safe_text(resp)}"
            )

        _write_bytes(out_path, resp.content)
        return TTSResult(
            audio_path=out_path,
            char_count=char_count,
            cost_usd=cost,
            word_timestamps=[],
        )

    # -- voice catalog / community -----------------------------------------
    async def list_voices(self) -> list[dict]:
        """GET /v1/voices — the account's available voices, normalized."""
        resp = await self._request(
            "GET", "/v1/voices", headers=self._headers()
        )
        if resp.status_code >= 400:
            raise ElevenLabsError(
                f"Failed to list voices ({resp.status_code}): {_safe_text(resp)}"
            )
        voices = resp.json().get("voices", []) or []
        return [
            {
                "name": v.get("name", ""),
                "voice_id": v.get("voice_id", ""),
                "category": v.get("category", ""),
                "labels": v.get("labels", {}) or {},
            }
            for v in voices
        ]

    async def add_shared_voice(
        self, public_user_id: str, voice_id: str, name: str
    ) -> dict:
        """POST /v1/voices/add/{public_user_id}/{voice_id} — add a community voice.

        Returns ``{"voice_id": <new id>}`` on success.
        """
        resp = await self._request(
            "POST",
            f"/v1/voices/add/{public_user_id}/{voice_id}",
            headers=self._headers(),
            json={"new_name": name},
        )
        if resp.status_code >= 400:
            raise ElevenLabsError(
                f"Failed to add shared voice ({resp.status_code}): "
                f"{_safe_text(resp)}"
            )
        return resp.json()

    async def browse_shared_voices(
        self,
        gender: str | None = None,
        language: str | None = None,
        category: str | None = None,
    ) -> list[dict]:
        """GET /v1/shared-voices — public community-voice library (paged page 0)."""
        params: dict[str, Any] = {"page_size": 100}
        if gender:
            params["gender"] = gender
        if language:
            params["language"] = language
        if category:
            params["category"] = category

        resp = await self._request(
            "GET", "/v1/shared-voices", headers=self._headers(), params=params
        )
        if resp.status_code >= 400:
            raise ElevenLabsError(
                f"Failed to browse shared voices ({resp.status_code}): "
                f"{_safe_text(resp)}"
            )
        voices = resp.json().get("voices", []) or []
        return [
            {
                "name": v.get("name", ""),
                "voice_id": v.get("voice_id", ""),
                "public_owner_id": v.get("public_owner_id", ""),
                "category": v.get("category", ""),
                "gender": (v.get("labels", {}) or {}).get("gender")
                or v.get("gender", ""),
                "language": v.get("language", ""),
                "labels": v.get("labels", {}) or {},
                "preview_url": v.get("preview_url", ""),
            }
            for v in voices
        ]


# -- module helpers ---------------------------------------------------------
def _write_bytes(path: str, data: bytes) -> None:
    import os

    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(data)


def _safe_text(resp: httpx.Response) -> str:
    try:
        return resp.text[:500]
    except Exception:
        return "<unreadable response body>"


def _chars_to_words(alignment: dict) -> list[dict]:
    """Collapse ElevenLabs character-level alignment into word timestamps.

    ElevenLabs returns parallel arrays:
        characters: list[str]
        character_start_times_seconds: list[float]
        character_end_times_seconds: list[float]

    A word boundary is any run of non-whitespace characters. Each word's
    ``start`` is the first character's start time and ``end`` is the last
    character's end time.
    """
    chars = alignment.get("characters") or []
    starts = alignment.get("character_start_times_seconds") or []
    ends = alignment.get("character_end_times_seconds") or []
    if not chars or len(chars) != len(starts) or len(chars) != len(ends):
        return []

    words: list[dict] = []
    cur_chars: list[str] = []
    cur_start: float | None = None
    cur_end: float = 0.0

    def flush() -> None:
        nonlocal cur_chars, cur_start, cur_end
        if cur_chars and cur_start is not None:
            word = "".join(cur_chars)
            if word.strip():
                words.append(
                    {
                        "word": word,
                        "start": round(float(cur_start), 3),
                        "end": round(float(cur_end), 3),
                    }
                )
        cur_chars = []
        cur_start = None
        cur_end = 0.0

    for ch, st, en in zip(chars, starts, ends):
        if ch.isspace():
            flush()
            continue
        if cur_start is None:
            cur_start = st
        cur_chars.append(ch)
        cur_end = en
    flush()

    return words


# Module-level singleton.
elevenlabs_service = ElevenLabsService()
