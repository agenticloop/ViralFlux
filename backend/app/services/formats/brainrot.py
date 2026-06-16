from __future__ import annotations

from .base import FormatPlugin, FormatOutput


class BrainrotFormat(FormatPlugin):
    """High-energy deadpan narration over CC0 satisfying loop footage."""

    genre = "brainrot"

    async def prepare(self, job, channel) -> FormatOutput:
        return await self._prepare(job, channel)
