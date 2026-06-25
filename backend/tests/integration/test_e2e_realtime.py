"""End-to-end checks for the realtime stream-token endpoint (RBAC + wiring)."""

from __future__ import annotations

from tests.integration.test_e2e_auth import _onboard_verify_login


async def test_stream_token_requires_auth(client):
    http, _ = client
    res = await http.post("/api/v1/realtime/token")
    assert res.status_code == 401


async def test_owner_gets_a_short_lived_stream_token(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(
        http, fake_email, slug="resto", email="owner@resto.com"
    )
    res = await http.post(
        "/api/v1/realtime/token",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["token"]
    assert body["expires_in"] == 60
