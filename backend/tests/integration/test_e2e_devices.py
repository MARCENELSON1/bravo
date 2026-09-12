"""Registro del push token del device (Fase 4): POST /devices, tenant+user scoped,
upsert idempotente por token."""

from __future__ import annotations

from tests.integration.test_e2e_auth import _onboard_verify_login
from tests.integration.test_e2e_payments import _auth


async def test_register_device_token(client):
    http, fake_email = client
    h = _auth(await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com"))

    res = await http.post(
        "/api/v1/devices",
        json={"token": "fcm-abc-123", "platform": "ios"},
        headers=h,
    )
    assert res.status_code == 204, res.text

    # Re-registrar el mismo token → 204 (upsert, sin duplicar ni romper).
    again = await http.post(
        "/api/v1/devices",
        json={"token": "fcm-abc-123", "platform": "ios"},
        headers=h,
    )
    assert again.status_code == 204, again.text


async def test_register_device_rejects_bad_platform(client):
    http, fake_email = client
    h = _auth(await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com"))
    res = await http.post(
        "/api/v1/devices",
        json={"token": "x", "platform": "windows"},
        headers=h,
    )
    assert res.status_code == 422


async def test_register_device_requires_auth(client):
    http, _ = client
    res = await http.post(
        "/api/v1/devices", json={"token": "x", "platform": "ios"}
    )
    assert res.status_code == 401
