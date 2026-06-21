"""End-to-end presence layer: provision device → rotating challenge → punch by
presenting the scanned/typed token (source=PRESENCE)."""

from __future__ import annotations

from tests.integration.test_e2e_auth import _onboard_verify_login


def _auth(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


async def test_presence_device_challenge_and_punch(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    h = _auth(tokens)

    device = await http.post("/api/v1/timeclock/presence/devices", headers=h)
    assert device.status_code == 201, device.text
    device_token = device.json()["device_token"]

    challenge = await http.get(
        "/api/v1/timeclock/presence/current", headers={"X-Device-Token": device_token}
    )
    assert challenge.status_code == 200, challenge.text
    code = challenge.json()["code"]
    assert code and challenge.json()["qr_payload"]

    punch = await http.post(
        "/api/v1/timeclock/presence/punch", json={"presented": code}, headers=h
    )
    assert punch.status_code == 200, punch.text
    assert punch.json()["status"] == "OPEN"
    assert punch.json()["source"] == "PRESENCE"

    # Replay of the same code by the same user → rejected.
    replay = await http.post(
        "/api/v1/timeclock/presence/punch", json={"presented": code}, headers=h
    )
    assert replay.status_code == 409
    assert replay.json()["code"] == "presence_token_reused"


async def test_presence_current_requires_device_token(client):
    http, fake_email = client
    await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    missing = await http.get("/api/v1/timeclock/presence/current")
    assert missing.status_code == 422  # required header absent

    bad = await http.get(
        "/api/v1/timeclock/presence/current", headers={"X-Device-Token": "garbage.deadbeef"}
    )
    assert bad.status_code == 401
    assert bad.json()["code"] == "invalid_presence_device"


async def test_presence_punch_with_bad_code_rejected(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    bad = await http.post(
        "/api/v1/timeclock/presence/punch",
        json={"presented": "ZZZZZZ"},
        headers=_auth(tokens),
    )
    assert bad.status_code == 401
    assert bad.json()["code"] == "invalid_presence_token"
