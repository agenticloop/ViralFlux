from __future__ import annotations

import asyncio
import logging

from sqlalchemy import select

from app.core import pricing
from app.core.genres import GENRES

logger = logging.getLogger(__name__)


def _plan_rows() -> list[dict]:
    rows = []
    for name in pricing.PLAN_NAMES:
        rows.append(
            {
                "name": name,
                "price_usd": pricing.PLAN_PRICE_MONTHLY[name],
                "price_yearly_usd": pricing.PLAN_PRICE_YEARLY[name],
                "credits_per_month": pricing.PLAN_CREDITS[name],
                "max_quota": pricing.MAX_QUOTA[name],
                "channels_limit": pricing.PLAN_CHANNELS[name],
                "features": pricing.plan_feature_dict(name),
            }
        )
    return rows


def _genre_rows() -> list[dict]:
    rows = []
    for slug, g in GENRES.items():
        rows.append(
            {
                "slug": slug,
                "name": g["name"],
                "description": g["description"],
                "is_active": slug in ("horror", "brainrot"),
                "min_plan": "pro" if slug == "custom" else "free",
            }
        )
    return rows


async def seed() -> None:
    from app.core.database import async_session_maker
    from app.models.blog import ContentFormat
    from app.models.plan import Plan

    async with async_session_maker() as session:
        # ── Plans ────────────────────────────────────────────────────────
        for plan_data in _plan_rows():
            result = await session.execute(
                select(Plan).where(Plan.name == plan_data["name"])
            )
            existing = result.scalar_one_or_none()
            if existing:
                # Keep plan economics in sync with pricing.py on every boot.
                for k, v in plan_data.items():
                    setattr(existing, k, v)
                logger.info("Updated plan: %s", plan_data["name"])
            else:
                session.add(Plan(**plan_data))
                logger.info("Seeded plan: %s", plan_data["name"])

        # ── Genres (stored in content_formats) ───────────────────────────
        for g in _genre_rows():
            result = await session.execute(
                select(ContentFormat).where(ContentFormat.slug == g["slug"])
            )
            existing = result.scalar_one_or_none()
            if existing:
                for k, v in g.items():
                    setattr(existing, k, v)
            else:
                session.add(ContentFormat(**g))
                logger.info("Seeded genre: %s", g["slug"])

        await session.commit()
        logger.info("Seed complete.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(seed())
