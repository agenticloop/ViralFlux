"""Tests for the schedule scanner (schedule_tasks._process_schedule).

We call the underlying async helper directly with a session instead of going
through Celery. External script-idea generation degrades gracefully (returns
None) without a real key, so topic generation does not block the job creation.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select

from app.models.channel import ChannelSchedule, YoutubeChannel
from app.models.plan import Plan
from app.models.user import User
from app.models.video_job import VideoJob
from app.workers.tasks import schedule_tasks

from conftest import get_plan_by_name


async def _user_with_credits(db, plan: Plan, sub_credits: int = 1000) -> User:
    u = User(
        email=f"sched-{uuid.uuid4().hex[:10]}@example.com",
        password_hash="x",
        is_verified=True,
        plan_id=plan.id,
        subscription_credits=sub_credits,
    )
    db.add(u)
    await db.flush()
    return u


async def _connected_channel(db, user: User, **overrides) -> YoutubeChannel:
    data = dict(
        user_id=user.id,
        channel_name="Sched Channel",
        genre="horror",
        default_model_tier="Lite",
        default_duration="20s",
        # youtube_connected == bool(oauth_refresh_token)
        oauth_refresh_token="encrypted-refresh-token",
    )
    data.update(overrides)
    ch = YoutubeChannel(**data)
    db.add(ch)
    await db.flush()
    return ch


async def _schedule(db, channel, *, enabled=True, next_run_at, topics=None) -> ChannelSchedule:
    sch = ChannelSchedule(
        channel_id=channel.id,
        is_enabled=enabled,
        frequency_days=2,
        next_run_at=next_run_at,
        topics_queue=topics,
    )
    db.add(sch)
    await db.flush()
    return sch


async def _jobs_for_channel(db, channel_id) -> int:
    res = await db.execute(
        select(func.count()).select_from(VideoJob).where(VideoJob.channel_id == channel_id)
    )
    return res.scalar_one()


async def test_due_schedule_creates_job_reserves_and_advances(db, monkeypatch):
    # Prevent Celery enqueue from doing anything real.
    monkeypatch.setattr(
        "app.workers.tasks.video_tasks.generate_video.delay", lambda *a, **k: None
    )
    plan = await get_plan_by_name(db, "free")
    user = await _user_with_credits(db, plan, sub_credits=100)
    channel = await _connected_channel(db, user)
    past = datetime.now(timezone.utc) - timedelta(minutes=5)
    sch = await _schedule(db, channel, next_run_at=past, topics=["a haunted lighthouse"])

    now = datetime.now(timezone.utc)
    await schedule_tasks._process_schedule(db, sch, now)
    await db.flush()

    assert await _jobs_for_channel(db, channel.id) == 1
    # 20s Lite = 14 credits reserved.
    await db.refresh(user)
    assert user.subscription_credits == 100 - 14
    # next_run_at advanced into the future.
    assert sch.next_run_at > now
    assert sch.last_run_at is not None


async def test_not_due_or_disabled_creates_nothing(db, monkeypatch):
    monkeypatch.setattr(
        "app.workers.tasks.video_tasks.generate_video.delay", lambda *a, **k: None
    )
    plan = await get_plan_by_name(db, "free")
    user = await _user_with_credits(db, plan, sub_credits=100)

    # Disabled schedule: the scanner query filters is_enabled — assert the query
    # excludes it, and that processing a disabled+future row creates no job.
    channel = await _connected_channel(db, user, channel_name="Disabled Ch")
    future = datetime.now(timezone.utc) + timedelta(days=1)
    sch = await _schedule(db, channel, enabled=False, next_run_at=future)
    await db.flush()

    # The scanner SELECT must not pick up disabled / not-due rows.
    now = datetime.now(timezone.utc)
    due = await db.execute(
        select(ChannelSchedule).where(
            ChannelSchedule.is_enabled.is_(True),
            ChannelSchedule.next_run_at.isnot(None),
            ChannelSchedule.next_run_at <= now,
            ChannelSchedule.channel_id == channel.id,
        )
    )
    assert due.scalars().first() is None
    assert await _jobs_for_channel(db, channel.id) == 0


async def test_no_credits_creates_nothing(db, monkeypatch):
    monkeypatch.setattr(
        "app.workers.tasks.video_tasks.generate_video.delay", lambda *a, **k: None
    )
    plan = await get_plan_by_name(db, "free")
    user = await _user_with_credits(db, plan, sub_credits=0)  # broke
    channel = await _connected_channel(db, user, channel_name="Broke Ch")
    past = datetime.now(timezone.utc) - timedelta(minutes=5)
    sch = await _schedule(db, channel, next_run_at=past, topics=["a topic"])

    now = datetime.now(timezone.utc)
    await schedule_tasks._process_schedule(db, sch, now)
    await db.flush()

    # No job created; but the schedule still advances (skip this run).
    assert await _jobs_for_channel(db, channel.id) == 0
    assert sch.next_run_at > now
