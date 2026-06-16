"""Provider-agnostic AI image generation for ViralFlux.

The horror visual path (``visual == "generated_images"``) turns each scene
description into a 9:16 vertical still via a text-to-image model, then the video
pipeline applies a ken-burns pan/zoom. The provider is selected by
``settings.IMAGE_PROVIDER`` so the underlying model can swap (Imagen → z-image →
gpt-image-mini) without touching the calling pipeline.

A *per-video seed* is threaded through every scene so a single video keeps a
consistent visual identity across its scenes.

No live API calls are made at import time. Providers raise a clear ``RuntimeError``
when their credentials are missing so failures are obvious and actionable.
"""
from __future__ import annotations

import asyncio
import base64
import logging
import os
from abc import ABC, abstractmethod

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

# Google AI Studio (Generative Language) REST endpoint for Imagen predict calls.
_GOOGLE_AI_BASE = "https://generativelanguage.googleapis.com/v1beta"

# Default aspect ratio for ViralFlux verticals (1080x1920).
_VERTICAL_ASPECT_RATIO = "9:16"

# Transient-failure retry policy (matches the LLM/TTS layers). Image generation
# is the most network-heavy pipeline step (one call per scene), so an occasional
# timeout / reset / 429-503 must not fail an otherwise-good video.
_MAX_RETRIES = 3
_BACKOFF_BASE = 1.0  # seconds, exponential
_RETRYABLE_STATUS = frozenset({429, 500, 502, 503, 504})


async def _post_with_retry(
    url: str, *, params: dict, json: dict, timeout: float, label: str
) -> dict:
    """POST with exponential-backoff retry on transient HTTP failures.

    Retries connection/read errors and retryable status codes; raises
    ``ImageGenerationError`` on a non-retryable status or after exhausting
    retries. Returns the decoded JSON body.
    """
    last_exc: Exception | None = None
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, params=params, json=json)
            if response.status_code in _RETRYABLE_STATUS:
                raise httpx.HTTPStatusError(
                    f"retryable status {response.status_code}",
                    request=response.request,
                    response=response,
                )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code if exc.response is not None else None
            if status not in _RETRYABLE_STATUS:
                body = exc.response.text[:500] if exc.response is not None else ""
                logger.error("%s HTTP %s: %s", label, status, body)
                raise ImageGenerationError(
                    f"{label} API returned HTTP {status}: {body}"
                ) from exc
            last_exc = exc
        except httpx.HTTPError as exc:
            last_exc = exc

        if attempt < _MAX_RETRIES:
            delay = _BACKOFF_BASE * (2 ** (attempt - 1))
            logger.warning(
                "%s request failed (attempt %d/%d): %r; retrying in %.1fs",
                label, attempt, _MAX_RETRIES, last_exc, delay,
            )
            await asyncio.sleep(delay)

    logger.exception("%s request failed after %d attempts", label, _MAX_RETRIES)
    raise ImageGenerationError(
        f"{label} request failed after {_MAX_RETRIES} attempts: {last_exc!r}"
    ) from last_exc


class ImageGenerationError(RuntimeError):
    """Raised when an image provider fails to generate an image."""


# ---------------------------------------------------------------------------
# Provider interface
# ---------------------------------------------------------------------------


class ImageProvider(ABC):
    """Abstract base for a single-image text-to-image generator.

    Implementations must be safe to construct even if credentials are missing;
    the credential check belongs in :meth:`generate` (or an explicit guard) so a
    missing key produces a clear runtime error rather than an import-time crash.
    """

    @abstractmethod
    async def generate(self, prompt: str, seed: int, out_path: str) -> str:
        """Generate one image for ``prompt`` and write it to ``out_path``.

        Args:
            prompt: The *full* image prompt (the caller is responsible for
                prepending the genre ``image_style_prefix``).
            seed: Deterministic seed; pass the same per-video seed across scenes
                for visual consistency.
            out_path: Absolute destination path for the generated image.

        Returns:
            The path the image was written to (echoes ``out_path``).
        """
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Imagen (Google AI Studio) — primary provider
# ---------------------------------------------------------------------------


class ImagenProvider(ImageProvider):
    """Google Imagen 4 Fast via the AI Studio Generative Language REST API.

    Uses the ``:predict`` endpoint for the model named by
    ``settings.IMAGEN_MODEL`` (default ``imagen-4.0-fast-generate-001``) and
    requests a single 9:16 vertical image per scene.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        *,
        timeout: float = 120.0,
    ) -> None:
        self.api_key = api_key if api_key is not None else settings.GOOGLE_AI_API_KEY
        self.model = model or settings.IMAGEN_MODEL
        self.timeout = timeout

    @property
    def _endpoint(self) -> str:
        return f"{_GOOGLE_AI_BASE}/models/{self.model}:predict"

    async def generate(self, prompt: str, seed: int, out_path: str) -> str:
        if not self.api_key:
            raise ImageGenerationError(
                "GOOGLE_AI_API_KEY is not set — cannot generate images with the "
                "Imagen provider. Set the key or switch settings.IMAGE_PROVIDER."
            )

        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)

        # NOTE: Imagen 4 Fast on the AI Studio (Generative Language) API rejects
        # both `seed` and `addWatermark` ("Setting <x> is not supported."). The
        # seed is therefore not threaded through this provider; visual coherence
        # across scenes is steered via the prompt/style prefix instead. The seed
        # argument is kept in the method signature for the provider contract and
        # for providers that DO support it.
        payload = {
            "instances": [{"prompt": prompt}],
            "parameters": {
                "sampleCount": 1,
                "aspectRatio": _VERTICAL_ASPECT_RATIO,
            },
        }

        logger.info(
            "Imagen generate: model=%s seed=%d -> %s", self.model, seed, out_path
        )

        data = await _post_with_retry(
            self._endpoint,
            params={"key": self.api_key},
            json=payload,
            timeout=self.timeout,
            label="Imagen",
        )

        image_bytes = self._extract_image_bytes(data)
        with open(out_path, "wb") as f:
            f.write(image_bytes)

        logger.info("Imagen wrote %d bytes to %s", len(image_bytes), out_path)
        return out_path

    @staticmethod
    def _extract_image_bytes(data: dict) -> bytes:
        """Pull base64 image bytes out of a ``:predict`` response.

        The AI Studio Imagen response shape is::

            {"predictions": [{"bytesBase64Encoded": "<b64>", "mimeType": "image/png"}]}
        """
        predictions = data.get("predictions") or []
        if not predictions:
            raise ImageGenerationError(
                f"Imagen response contained no predictions: {str(data)[:300]}"
            )

        first = predictions[0]
        b64 = first.get("bytesBase64Encoded") or first.get("image")
        if not b64:
            raise ImageGenerationError(
                f"Imagen prediction missing image bytes: {str(first)[:300]}"
            )
        try:
            return base64.b64decode(b64)
        except (ValueError, TypeError) as exc:
            raise ImageGenerationError(
                f"Could not decode Imagen base64 image: {exc}"
            ) from exc


# ---------------------------------------------------------------------------
# Nano Banana Pro (Gemini 3 Pro Image) — premium provider
# ---------------------------------------------------------------------------


class NanoBananaProvider(ImageProvider):
    """Google "Nano Banana Pro" = Gemini 3 Pro Image, via ``generateContent``.

    Unlike Imagen's ``:predict`` shape, the Gemini image models return the image
    inline in a content part (``inlineData`` with base64). Higher quality/coherence
    than Imagen 4 Fast, at higher cost — exposed as a premium swap via
    ``IMAGE_PROVIDER=nanobanana`` and its own dedicated key.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        *,
        timeout: float = 180.0,
    ) -> None:
        # Falls back to the main Google AI key if the dedicated one is unset.
        self.api_key = (
            api_key
            if api_key is not None
            else (settings.NANO_BANANA_PRO_API_KEY or settings.GOOGLE_AI_API_KEY)
        )
        self.model = model or settings.NANO_BANANA_MODEL
        self.timeout = timeout

    @property
    def _endpoint(self) -> str:
        return f"{_GOOGLE_AI_BASE}/models/{self.model}:generateContent"

    async def generate(self, prompt: str, seed: int, out_path: str) -> str:
        if not self.api_key:
            raise ImageGenerationError(
                "NANO_BANANA_PRO_API_KEY / GOOGLE_AI_API_KEY is not set — cannot "
                "generate images with the Nano Banana provider."
            )

        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)

        # Nudge the model toward a 9:16 vertical still; it doesn't take an explicit
        # aspectRatio param, so we steer via the prompt.
        full_prompt = f"{prompt}\n\nVertical 9:16 aspect ratio, full-bleed composition."
        payload = {
            "contents": [{"parts": [{"text": full_prompt}]}],
            "generationConfig": {"responseModalities": ["IMAGE"]},
        }

        logger.info(
            "NanoBanana generate: model=%s seed=%d -> %s", self.model, seed, out_path
        )

        data = await _post_with_retry(
            self._endpoint,
            params={"key": self.api_key},
            json=payload,
            timeout=self.timeout,
            label="NanoBanana",
        )

        image_bytes = self._extract_image_bytes(data)
        with open(out_path, "wb") as f:
            f.write(image_bytes)

        logger.info("NanoBanana wrote %d bytes to %s", len(image_bytes), out_path)
        return out_path

    @staticmethod
    def _extract_image_bytes(data: dict) -> bytes:
        """Pull base64 image bytes from a ``generateContent`` image response."""
        candidates = data.get("candidates") or []
        if not candidates:
            raise ImageGenerationError(
                f"NanoBanana response had no candidates: {str(data)[:300]}"
            )
        parts = (candidates[0].get("content") or {}).get("parts") or []
        for part in parts:
            inline = part.get("inlineData") or part.get("inline_data")
            if inline and inline.get("data"):
                try:
                    return base64.b64decode(inline["data"])
                except (ValueError, TypeError) as exc:
                    raise ImageGenerationError(
                        f"Could not decode NanoBanana base64 image: {exc}"
                    ) from exc
        raise ImageGenerationError(
            f"NanoBanana response contained no image part: {str(data)[:300]}"
        )


# ---------------------------------------------------------------------------
# Swap-in stubs
# ---------------------------------------------------------------------------


class ZImageProvider(ImageProvider):
    """Stub for the z-image provider (swap-in point)."""

    async def generate(self, prompt: str, seed: int, out_path: str) -> str:
        # TODO(viralflux): Implement z-image generation. Wire up the z-image
        # HTTP/SDK client here, request a 9:16 image with the given seed, and
        # write the decoded bytes to out_path. Mirror ImagenProvider.generate.
        raise NotImplementedError(
            "ZImageProvider is not implemented yet. Set IMAGE_PROVIDER=imagen "
            "or implement this provider."
        )


class GptImageProvider(ImageProvider):
    """Stub for the gpt-image-mini provider (swap-in point)."""

    async def generate(self, prompt: str, seed: int, out_path: str) -> str:
        # TODO(viralflux): Implement gpt-image-mini generation. Call the OpenAI
        # images API (size 1024x1792 for vertical), decode the b64_json result,
        # and write to out_path. Mirror ImagenProvider.generate.
        raise NotImplementedError(
            "GptImageProvider is not implemented yet. Set IMAGE_PROVIDER=imagen "
            "or implement this provider."
        )


# ---------------------------------------------------------------------------
# Factory + singleton service
# ---------------------------------------------------------------------------


def get_image_provider() -> ImageProvider:
    """Build the configured :class:`ImageProvider` from ``settings.IMAGE_PROVIDER``."""
    provider = (settings.IMAGE_PROVIDER or "imagen").lower()
    if provider == "imagen":
        return ImagenProvider()
    if provider in ("nanobanana", "nano", "nano_banana"):
        return NanoBananaProvider()
    if provider == "zimage":
        return ZImageProvider()
    if provider == "gptimage":
        return GptImageProvider()
    raise ImageGenerationError(
        f"Unknown IMAGE_PROVIDER '{settings.IMAGE_PROVIDER}'. "
        "Expected one of: imagen, nanobanana, zimage, gptimage."
    )


class ImageService:
    """High-level scene-image generator used by the video pipeline.

    Lazily resolves the configured provider so importing this module never
    requires credentials.
    """

    def __init__(self, provider: ImageProvider | None = None) -> None:
        self._provider = provider

    @property
    def provider(self) -> ImageProvider:
        if self._provider is None:
            self._provider = get_image_provider()
        return self._provider

    async def generate_scene_images(
        self, prompts: list[str], seed: int, out_dir: str
    ) -> list[str]:
        """Generate one image per prompt, in order, sharing one per-video seed.

        Args:
            prompts: Full per-scene prompts (genre style prefix already applied).
            seed: Per-video seed shared across all scenes for visual consistency.
            out_dir: Directory to write ``scene_000.png`` … into.

        Returns:
            Ordered list of written file paths, one per input prompt.
        """
        os.makedirs(out_dir, exist_ok=True)
        paths: list[str] = []
        for i, prompt in enumerate(prompts):
            out_path = os.path.join(out_dir, f"scene_{i:03d}.png")
            written = await self.provider.generate(prompt, seed, out_path)
            paths.append(written)
        logger.info("Generated %d scene images in %s", len(paths), out_dir)
        return paths


# Module-level singleton.
image_service = ImageService()
