from __future__ import annotations

from .base import FormatPlugin, FormatOutput


class RankingFormat(FormatPlugin):
    """Ranking / Listicle format — "Top 5 Scariest…" style countdown videos.

    This format is planned for Phase 2 and is not yet implemented.
    """

    slug = "ranking"
    name = "Ranking / Listicle"
    min_plan = "creator"

    async def prepare(
        self,
        topic: str | None,
        channel_config: dict,
    ) -> FormatOutput:
        raise NotImplementedError("Ranking format coming in Phase 2")

    def estimate_cost(self, char_count: int) -> float:
        return 0.005
