from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.workers.celery_app import celery_app
from app.core.database import async_session_maker
from app.core import pricing
from app.models.channel import YoutubeChannel, ChannelSchedule
from app.models.user import User
from app.models.video_job import VideoJob

logger = logging.getLogger(__name__)


@celery_app.task
def scan_schedules():
    """Beat task: find due channel schedules and enqueue one video each.

    Runs every 5 minutes. Each due row is locked with FOR UPDATE SKIP LOCKED for
    multi-worker safety and committed independently so one failure can't block
    the rest.
    """
    asyncio.run(_scan_schedules_async())


async def _scan_schedules_async() -> None:
    now = datetime.now(timezone.utc)

    async with async_session_maker() as session:
        due_result = await session.execute(
            select(ChannelSchedule)
            .where(
                ChannelSchedule.is_enabled.is_(True),
                ChannelSchedule.next_run_at.isnot(None),
                ChannelSchedule.next_run_at <= now,
            )
            .with_for_update(skip_locked=True)
        )
        schedules = due_result.scalars().all()
        logger.info("scan_schedules: %d due schedule(s)", len(schedules))

        for schedule in schedules:
            try:
                await _process_schedule(session, schedule, now)
                await session.commit()
            except Exception as exc:
                await session.rollback()
                logger.exception(
                    "scan_schedules: failed processing schedule %s: %s",
                    schedule.id,
                    exc,
                )


async def _process_schedule(session, schedule, now: datetime) -> None:
    from app.services import credit_service

    # --- load channel ---
    ch_result = await session.execute(
        select(YoutubeChannel).where(YoutubeChannel.id == schedule.channel_id)
    )
    channel = ch_result.scalar_one_or_none()
    if not channel:
        logger.warning("Schedule %s has no channel — disabling", schedule.id)
        schedule.is_enabled = False
        return

    # --- gate: channel must be connected ---
    if not channel.youtube_connected:
        logger.info("Schedule %s skipped — channel not connected", schedule.id)
        _advance(schedule, now)
        return

    # --- gate: free-plan block window ---
    if schedule.block_ends_at and schedule.block_ends_at > now:
        logger.info("Schedule %s blocked until %s", schedule.id, schedule.block_ends_at)
        _advance(schedule, now)
        return

    # --- load user (+plan) ---
    u_result = await session.execute(
        select(User).options(selectinload(User.plan)).where(User.id == channel.user_id)
    )
    user = u_result.scalar_one_or_none()
    if not user:
        logger.warning("Schedule %s has no user — disabling", schedule.id)
        schedule.is_enabled = False
        return
    plan = user.plan

    # --- pick a topic ---
    topic = _pop_topic(schedule)
    if topic is None:
        topic = await _generate_topic(channel)

    # --- resolve model + duration from channel defaults ---
    requested_model = channel.default_model_tier or "Lite"
    if plan is not None:
        model_tier, fell_back = await credit_service.resolve_model_tier(
            session, user, plan, requested_model
        )
        if fell_back:
            logger.info(
                "Schedule %s: model %s fell back to %s",
                schedule.id, requested_model, model_tier,
            )
    else:
        model_tier = requested_model

    duration_tier = channel.default_duration or "30s"
    credits_cost = pricing.credits_for_video(duration_tier, model_tier)

    # --- affordability gate ---
    if not credit_service.can_afford(user, credits_cost):
        logger.info(
            "Schedule %s: user %s cannot afford %d credits — skipping run",
            schedule.id, user.id, credits_cost,
        )
        _advance(schedule, now)
        return

    # --- create job, reserve credits, enqueue ---
    job = VideoJob(
        id=uuid.uuid4(),
        user_id=user.id,
        channel_id=channel.id,
        genre=channel.genre,
        duration_tier=duration_tier,
        model_tier=model_tier,
        script_source="seed",
        topic=topic,
        status="queued",
        credits_cost=credits_cost,
    )
    session.add(job)
    await session.flush()  # assign job.id in DB

    await credit_service.reserve_for_video(
        session, user, duration=duration_tier, model=model_tier, job_id=job.id
    )

    from app.workers.tasks.video_tasks import generate_video

    generate_video.delay(str(job.id))
    _advance(schedule, now)
    logger.info(
        "Schedule %s: queued job %s (genre=%s, %s, %s, %d credits)",
        schedule.id, job.id, channel.genre, duration_tier, model_tier, credits_cost,
    )


def _pop_topic(schedule) -> str | None:
    """Pop the next queued topic off the schedule, if any."""
    queue = list(schedule.topics_queue or [])
    if not queue:
        return None
    topic = queue.pop(0)
    schedule.topics_queue = queue
    return topic


async def _generate_topic(channel) -> str | None:
    """Generate a single seed idea for the channel's genre, degrading gracefully."""
    try:
        from app.services.llm import gemini_service

        ideas = await gemini_service.generate_seed_ideas(
            genre=channel.genre,
            weekly_seed=channel.seed_prompt,
            count=1,
            model_tier=channel.default_model_tier or "Lite",
        )
        return ideas[0] if ideas else None
    except Exception as exc:
        logger.warning("Seed-idea generation failed for channel %s: %s", channel.id, exc)
        return None


def _advance(schedule, now: datetime) -> None:
    """Mark this run done and schedule the next one."""
    freq_days = int(getattr(schedule, "frequency_days", 0) or 2)
    schedule.last_run_at = now
    schedule.next_run_at = now + timedelta(days=freq_days)
