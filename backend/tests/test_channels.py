"""Integration tests for channel CRUD, plan gating, and multi-tenant isolation."""
from __future__ import annotations

from conftest import register_verify_login


async def _create_channel(client, headers, **overrides):
    payload = {
        "channel_name": "My Horror Channel",
        "genre": "horror",
        "default_model_tier": "Lite",
        "default_duration": "20s",
    }
    payload.update(overrides)
    return await client.post("/api/v1/channels/", json=payload, headers=headers)


async def test_create_list_channel(auth, client):
    res = await _create_channel(client, auth["headers"])
    assert res.status_code == 201, res.text
    ch = res.json()
    assert ch["channel_name"] == "My Horror Channel"
    assert ch["genre"] == "horror"
    assert ch["youtube_connected"] is False

    lst = await client.get("/api/v1/channels/", headers=auth["headers"])
    assert lst.status_code == 200
    assert any(c["id"] == ch["id"] for c in lst.json())


async def test_genre_validated_against_plan(auth, client):
    # 'custom' genre is Pro+ only -> free plan must be rejected with 402.
    res = await _create_channel(client, auth["headers"], genre="custom")
    assert res.status_code == 402, res.text


async def test_unknown_genre_rejected(auth, client):
    res = await _create_channel(client, auth["headers"], genre="nonsense")
    assert res.status_code == 422


async def test_update_seed_prompt_stamps_timestamp(auth, client):
    res = await _create_channel(client, auth["headers"])
    ch_id = res.json()["id"]
    assert res.json()["seed_prompt_updated_at"] is None

    upd = await client.put(
        f"/api/v1/channels/{ch_id}",
        json={"seed_prompt": "spooky abandoned hospital"},
        headers=auth["headers"],
    )
    assert upd.status_code == 200, upd.text
    body = upd.json()
    assert body["seed_prompt"] == "spooky abandoned hospital"
    assert body["seed_prompt_updated_at"] is not None


async def test_free_plan_channel_limit_one(auth, client):
    first = await _create_channel(client, auth["headers"], channel_name="Ch1")
    assert first.status_code == 201
    second = await _create_channel(client, auth["headers"], channel_name="Ch2")
    # free plan channels_limit == 1 -> second create rejected.
    assert second.status_code == 402, second.text


async def test_multi_tenant_isolation(client):
    a = await register_verify_login(client)
    b = await register_verify_login(client)

    res = await _create_channel(client, a["headers"], channel_name="A-owned")
    assert res.status_code == 201
    ch_id = res.json()["id"]

    # User B cannot GET user A's channel.
    got = await client.get(f"/api/v1/channels/{ch_id}", headers=b["headers"])
    assert got.status_code == 404

    # User B cannot PUT user A's channel.
    put = await client.put(
        f"/api/v1/channels/{ch_id}",
        json={"channel_name": "hijacked"},
        headers=b["headers"],
    )
    assert put.status_code == 404


async def test_channel_voices_returns_genre_voices(auth, client):
    res = await _create_channel(client, auth["headers"], genre="horror")
    ch_id = res.json()["id"]
    voices = await client.get(
        f"/api/v1/channels/{ch_id}/voices", headers=auth["headers"]
    )
    assert voices.status_code == 200
    data = voices.json()["voices"]
    assert len(data) > 0
    assert all("voice_id" in v and "name" in v for v in data)
    # Horror's default narrator (Bill) is present.
    assert any(v["voice_id"] == "pqHfZKP75CvOlQylNhV4" for v in data)
