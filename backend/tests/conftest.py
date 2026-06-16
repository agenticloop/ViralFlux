"""Shared pytest fixtures for the ViralFlux backend suite.

Runs INSIDE the backend container against a SEPARATE `viralflux_test` database so
dev data is never clobbered. ``DATABASE_URL`` is forced to the test DB *before*
any app module is imported, so the app engine binds to it.
"""
from __future__ import annotations

import os
import uuid

# --- point the app at the test DB BEFORE importing any app module -----------
TEST_DATABASE_URL = (
    "postgresql+asyncpg://viralflux_user:change-me-strong-db-password"
    "@postgres:5432/viralflux_test"
)
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
import redis.asyncio as aioredis  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy import select  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.core.database import Base, async_session_maker, engine  # noqa: E402

# Import every model module so Base.metadata is fully populated before create_all.
from app.models import analytics, blog, channel, credits, plan, user, video_job  # noqa: E402,F401
from app.main import app  # noqa: E402
from app.seed import seed  # noqa: E402


# ---------------------------------------------------------------- DB lifecycle
@pytest_asyncio.fixture(scope="session", autouse=True)
async def _prepare_database():
    """Drop + recreate all tables once per session, then seed plans/genres."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await seed()
    yield
    await engine.dispose()


@pytest_asyncio.fixture
async def db():
    """A session bound to the test DB, committed on exit (mirrors get_db)."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        finally:
            await session.close()


# ---------------------------------------------------------------- HTTP client
@pytest_asyncio.fixture
async def client():
    """httpx AsyncClient driving the FastAPI app in-process (ASGI transport)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ---------------------------------------------------------------- helpers
def _unique_email(prefix: str = "user") -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}@example.com"


async def _read_otp(email: str) -> str:
    """Read the OTP the app stored in Redis under `otp:{email}`."""
    r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        otp = await r.get(f"otp:{email}")
    finally:
        await r.aclose()
    assert otp, f"No OTP found in Redis for {email}"
    return otp


async def register_verify_login(client: AsyncClient, email: str | None = None,
                                password: str = "SuperSecret123") -> dict:
    """Full onboarding: register → read OTP from Redis → verify → return auth ctx.

    Returns {email, password, access_token, user, headers}.
    """
    email = email or _unique_email()
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Test User"},
    )
    assert reg.status_code == 201, reg.text

    otp = await _read_otp(email)
    ver = await client.post(
        "/api/v1/auth/verify-otp", json={"email": email, "otp": otp}
    )
    assert ver.status_code == 200, ver.text
    body = ver.json()
    token = body["access_token"]
    return {
        "email": email,
        "password": password,
        "access_token": token,
        "user": body["user"],
        "headers": {"Authorization": f"Bearer {token}"},
        "refresh_cookie": ver.cookies.get("refresh_token"),
    }


@pytest_asyncio.fixture
async def auth(client):
    """A freshly registered + verified user on the free plan (30 credits)."""
    return await register_verify_login(client)


# ---------------------------------------------------------------- DB lookups
async def get_user_by_email(db, email: str):
    res = await db.execute(select(user.User).where(user.User.email == email))
    return res.scalar_one()


async def get_plan_by_name(db, name: str):
    res = await db.execute(select(plan.Plan).where(plan.Plan.name == name))
    return res.scalar_one()


# Export helpers as fixtures-callable names.
pytest.register_assert_rewrite  # noqa: B018  (keep import used)
