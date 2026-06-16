from __future__ import annotations

from .base import FormatPlugin
from .horror_story import HorrorFormat
from .brainrot import BrainrotFormat
from .ranking import CustomFormat

_REGISTRY: dict[str, FormatPlugin] = {}

_FALLBACK_GENRE = "horror"


def register(plugin: FormatPlugin) -> None:
    """Register a FormatPlugin under its genre slug."""
    _REGISTRY[plugin.genre] = plugin


def get_format_plugin(genre: str) -> FormatPlugin:
    """Return the FormatPlugin for a genre slug, falling back to horror."""
    return _REGISTRY.get(genre) or _REGISTRY[_FALLBACK_GENRE]


def list_formats() -> list[dict]:
    """Return a summary list of all registered formats."""
    return [{"genre": p.genre} for p in _REGISTRY.values()]


# Auto-register all built-in genre formats on import.
register(HorrorFormat())
register(BrainrotFormat())
register(CustomFormat())
