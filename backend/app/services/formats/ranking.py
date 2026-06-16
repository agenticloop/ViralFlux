from __future__ import annotations

from .base import FormatPlugin, FormatOutput


class CustomFormat(FormatPlugin):
    """User-defined genre (Pro+). Uses the generated-images path like horror.

    The old Reddit/listicle "ranking" logic is gone; this module now hosts the
    custom genre, which shares the shared generated-images preparation path.
    """

    genre = "custom"

    async def prepare(self, job, channel) -> FormatOutput:
        return await self._prepare(job, channel)
