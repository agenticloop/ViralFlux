from __future__ import annotations

from .base import FormatPlugin, FormatOutput


class BrainrotFormat(FormatPlugin):
    """Brainrot Dialogue format — two AI personas arguing over absurd topics.

    This format is planned for Phase 2 and is not yet implemented.
    """

    slug = "brainrot"
    name = "Brainrot Dialogue"
    min_plan = "creator"

    async def prepare(
        self,
        topic: str | None,
        channel_config: dict,
    ) -> FormatOutput:
        raise NotImplementedError("Brainrot format coming in Phase 2")

    def estimate_cost(self, char_count: int) -> float:
        return 0.005
