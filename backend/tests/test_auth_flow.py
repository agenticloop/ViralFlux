"""Integration tests for the auth flow via httpx AsyncClient."""
from __future__ import annotations

from conftest import _read_otp, _unique_email, register_verify_login


async def test_register_verify_me_grants_free_plan_30_credits(client):
    ctx = await register_verify_login(client)

    me = await client.get("/api/v1/auth/me", headers=ctx["headers"])
    assert me.status_code == 200, me.text
    body = me.json()
    assert body["email"] == ctx["email"]
    assert body["is_verified"] is True
    assert body["plan_id"] is not None  # free plan assigned

    # Free plan grants 30 credits on verify (UserOut omits credit fields, so
    # read the wallet via /plans/current).
    cur = await client.get("/api/v1/plans/current", headers=ctx["headers"])
    assert cur.status_code == 200, cur.text
    usage = cur.json()["usage"]
    assert usage["subscription_credits"] == 30
    assert usage["credits_balance"] == 30


async def test_login_after_verify(client):
    ctx = await register_verify_login(client)
    res = await client.post(
        "/api/v1/auth/login",
        json={"email": ctx["email"], "password": ctx["password"]},
    )
    assert res.status_code == 200, res.text
    assert res.json()["access_token"]


async def test_refresh_issues_new_access_token(client):
    ctx = await register_verify_login(client)
    # The verify response set a refresh cookie on the client's cookie jar.
    res = await client.post("/api/v1/auth/refresh")
    assert res.status_code == 200, res.text
    assert res.json()["access_token"]


async def test_refresh_without_cookie_rejected(client):
    # Fresh client state: clear cookies first.
    client.cookies.clear()
    res = await client.post("/api/v1/auth/refresh")
    assert res.status_code == 401


async def test_duplicate_register_rejected(client):
    email = _unique_email()
    await register_verify_login(client, email=email)
    dup = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "SuperSecret123"},
    )
    assert dup.status_code == 409


async def test_wrong_otp_rejected(client):
    email = _unique_email()
    reg = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "SuperSecret123"},
    )
    assert reg.status_code == 201
    # Confirm a real OTP exists, then submit a different one.
    real = await _read_otp(email)
    bad = "000000" if real != "000000" else "111111"
    res = await client.post(
        "/api/v1/auth/verify-otp", json={"email": email, "otp": bad}
    )
    assert res.status_code == 400


async def test_me_requires_auth(client):
    res = await client.get("/api/v1/auth/me")
    assert res.status_code == 401
