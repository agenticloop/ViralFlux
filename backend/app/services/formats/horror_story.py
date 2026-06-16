from __future__ import annotations

from .base import FormatPlugin, FormatOutput


class HorrorFormat(FormatPlugin):
    """Horror narration over AI-generated cinematic scenes (ken-burns)."""

    genre = "horror"

    async def prepare(self, job, channel) -> FormatOutput:
        return await self._prepare(job, channel)
