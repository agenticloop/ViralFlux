"""Asset services for ViralFlux.

Three asset sources, exposed as ready-to-use singletons:

* ``image_service``    — AI scene-image generation (horror visual path).
* ``footage_library``  — CC0 satisfying-loop footage (brainrot visual path).
* ``music_library``    — CC0 background music, selected per genre music bucket.
"""
from __future__ import annotations

from .image_service import (
    GptImageProvider,
    ImageGenerationError,
    ImagenProvider,
    ImageProvider,
    ImageService,
    ZImageProvider,
    get_image_provider,
    image_service,
)
from .footage_library import FootageLibrary, footage_library
from .music_library import MusicLibrary, music_library

__all__ = [
    # Image generation
    "ImageProvider",
    "ImagenProvider",
    "ZImageProvider",
    "GptImageProvider",
    "ImageService",
    "ImageGenerationError",
    "get_image_provider",
    "image_service",
    # Footage
    "FootageLibrary",
    "footage_library",
    # Music
    "MusicLibrary",
    "music_library",
]
