"""E2E de GET /me (Identidad Wellnod): whoami con nombres humanos."""

from __future__ import annotations

from httpx import AsyncClient

from tests.fakes import FakeEmailSender
from tests.integration.test_e2e_auth import (
    PASSWORD,
    _login,
    _onboard_verify_login,
    _verify_last_email,
)


def _auth(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


async def _onboard_named(
    http: AsyncClient, *, slug: str, email: str, owner_name: str
) -> None:
    response = await http.post(
        "/api/v1/tenants/onboarding",
        json={
            "tenant_name": "La Trattoria",
            "tenant_slug": slug,
            "owner_email": email,
            "owner_password": PASSWORD,
            "owner_name": owner_name,
        },
    )
    assert response.status_code == 201, response.text


async def test_me_returns_user_and_tenant_names(client):
    http, fake_email = client
    await _onboard_named(http, slug="trattoria", email="juan@resto.com", owner_name="Juan Pérez")
    await _verify_last_email(http, fake_email)
    tokens = await _login(http, slug="trattoria", email="juan@resto.com", password=PASSWORD)

    me = await http.get("/api/v1/me", headers=_auth(tokens))
    assert me.status_code == 200, me.text
    body = me.json()
    assert body["name"] == "Juan Pérez"
    assert body["email"] == "juan@resto.com"
    assert body["tenant_name"] == "La Trattoria"
    assert body["role"] == "OWNER"
    assert body["tenant_id"] and body["user_id"]


async def test_me_without_name_degrades_gracefully(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="bar", email="x@bar.com")

    me = await http.get("/api/v1/me", headers=_auth(tokens))
    assert me.status_code == 200, me.text
    body = me.json()
    assert body["name"] is None
    assert body["tenant_name"] == "Resto"  # el tenant_name del helper de onboarding


async def test_me_requires_auth(client):
    http, _ = client
    assert (await http.get("/api/v1/me")).status_code == 401
