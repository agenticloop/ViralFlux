from __future__ import annotations

import asyncio
import logging

from sqlalchemy import select

logger = logging.getLogger(__name__)

PLANS = [
    {
        "name": "starter",
        "price_usd": 29,
        "shorts_per_month": 20,
        "channels_limit": 1,
        "features": {
            "formats": ["horror_story", "motivational"],
            "voices": ["edge-tts"],
            "analytics": "basic",
            "approval": "email",
            "ai_topics": False,
            "api_access": False,
        },
    },
    {
        "name": "creator",
        "price_usd": 79,
        "shorts_per_month": 100,
        "channels_limit": 5,
        "features": {
            "formats": ["horror_story", "motivational", "brainrot", "ranking"],
            "voices": ["edge-tts", "elevenlabs", "google-tts"],
            "analytics": "full",
            "approval": "auto",
            "ai_topics": True,
            "api_access": False,
        },
    },
    {
        "name": "agency",
        "price_usd": 199,
        "shorts_per_month": None,
        "channels_limit": None,
        "features": {
            "formats": ["horror_story", "motivational", "brainrot", "ranking", "clip_stitch"],
            "voices": ["edge-tts", "elevenlabs", "google-tts", "openai-tts"],
            "analytics": "full",
            "approval": "auto",
            "ai_topics": True,
            "api_access": True,
            "white_label": True,
        },
    },
]

FORMATS = [
    {
        "slug": "horror_story",
        "name": "Horror Story",
        "description": "Reddit creepypasta narrated over atmospheric imagery",
        "is_active": True,
        "min_plan": "starter",
    },
    {
        "slug": "brainrot",
        "name": "Brainrot Dialogue",
        "description": "Two AI characters debating over gameplay footage",
        "is_active": False,
        "min_plan": "creator",
    },
    {
        "slug": "ranking",
        "name": "Ranking / Listicle",
        "description": "Top-N listicle with stock video clips",
        "is_active": False,
        "min_plan": "creator",
    },
    {
        "slug": "motivational",
        "name": "Motivational Quotes",
        "description": "Deep voice reading stoic quotes over cinematic backgrounds",
        "is_active": False,
        "min_plan": "starter",
    },
    {
        "slug": "clip_stitch",
        "name": "Clip Stitch",
        "description": "AI-stitched trending clips with commentary voiceover",
        "is_active": False,
        "min_plan": "agency",
    },
]


async def seed() -> None:
    from app.core.database import async_session_maker
    from app.models.blog import ContentFormat
    from app.models.plan import Plan

    async with async_session_maker() as session:
        # Seed plans
        for plan_data in PLANS:
            result = await session.execute(
                select(Plan).where(Plan.name == plan_data["name"])
            )
            if not result.scalar_one_or_none():
                plan = Plan(**plan_data)
                session.add(plan)
                logger.info("Seeded plan: %s", plan_data["name"])

        # Seed content formats
        for fmt_data in FORMATS:
            result = await session.execute(
                select(ContentFormat).where(ContentFormat.slug == fmt_data["slug"])
            )
            if not result.scalar_one_or_none():
                fmt = ContentFormat(**fmt_data)
                session.add(fmt)
                logger.info("Seeded format: %s", fmt_data["slug"])

        await session.commit()
        logger.info("Seed complete.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(seed())
