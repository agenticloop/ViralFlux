from __future__ import annotations

from .base import FormatPlugin
from .horror_story import HorrorStoryFormat
from .brainrot import BrainrotFormat
from .ranking import RankingFormat

_REGISTRY: dict[str, FormatPlugin] = {}


def register(plugin: FormatPlugin) -> None:
    """Register a FormatPlugin under its slug."""
    _REGISTRY[plugin.slug] = plugin


def get_format_plugin(slug: str) -> FormatPlugin:
    """Return the registered FormatPlugin for the given slug.

    Raises ValueError if the slug is not registered.
    """
    if slug not in _REGISTRY:
        raise ValueError(
            f"Unknown format: '{slug}'. "
            f"Available formats: {sorted(_REGISTRY.keys())}"
        )
    return _REGISTRY[slug]


def list_formats() -> list[dict]:
    """Return a summary list of all registered formats."""
    return [
        {
            "slug": plugin.slug,
            "name": plugin.name,
            "min_plan": plugin.min_plan,
        }
        for plugin in _REGISTRY.values()
    ]


# Auto-register all built-in formats on import
register(HorrorStoryFormat())
register(BrainrotFormat())
register(RankingFormat())
