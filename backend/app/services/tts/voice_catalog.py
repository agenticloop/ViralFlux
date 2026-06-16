from __future__ import annotations

import logging

from app.core.genres import get_genre

from .elevenlabs import ElevenLabsError, elevenlabs_service

logger = logging.getLogger(__name__)


class VoiceCatalog:
    """In-memory cache of the account's ElevenLabs voices.

    Populated best-effort at boot via :meth:`refresh`. If the API key is empty
    or the call fails, the cache simply stays empty — callers should treat
    ``get_all()`` as best-effort and rely on the curated per-genre voices from
    ``app/core/genres.py`` for the guaranteed baseline.
    """

    def __init__(self) -> None:
        self._voices: list[dict] = []
        self._loaded: bool = False

    async def refresh(self) -> list[dict]:
        """(Re)load voices from ElevenLabs. No-op-safe if the key is empty."""
        try:
            self._voices = await elevenlabs_service.list_voices()
            self._loaded = True
            logger.info("Voice catalog refreshed: %d voices", len(self._voices))
        except ElevenLabsError as exc:
            # Missing key or transient failure — keep whatever we had.
            logger.info("Voice catalog refresh skipped/failed: %s", exc)
        except Exception:  # pragma: no cover - defensive at boot
            logger.exception("Unexpected error refreshing voice catalog")
        return self._voices

    def get_all(self) -> list[dict]:
        """Return the cached voices (possibly empty)."""
        return list(self._voices)

    @property
    def loaded(self) -> bool:
        return self._loaded


def recommended_voices(genre: str) -> list[dict]:
    """Curated premade voices for a genre, straight from genres.py.

    Each entry is ``{name, voice_id, desc}``. Always available regardless of
    API key state.
    """
    return list(get_genre(genre).get("voices", []))


# Module-level singleton.
voice_catalog = VoiceCatalog()
