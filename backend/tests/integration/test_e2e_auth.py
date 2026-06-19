"""End-to-end auth flows over HTTP against the real app + DB (email faked)."""

from __future__ import annotations

from httpx import AsyncClient

from tests.fakes import FakeEmailSender

PASSWORD = "Sup3rSecret!"


def _token_from_link(link: str) -> str:
    return link.split("token=", 1)[1]


async def _onboard(
    http: AsyncClient, fake_email: FakeEmailSender, *, slug: str, email: str
) -> None:
    response = await http.post(
        "/api/v1/tenants/onboarding",
        json={
            "tenant_name": "Resto",
            "tenant_slug": slug,
            "owner_email": email,
            "owner_password": PASSWORD,
        },
    )
    assert response.status_code == 201, response.text


async def _verify_last_email(http: AsyncClient, fake_email: FakeEmailSender) -> None:
    token = _token_from_link(fake_email.last().link)
    response = await http.post("/api/v1/auth/verify-email", json={"token": token})
    assert response.status_code == 200, response.text


async def _login(http: AsyncClient, *, slug: str, email: str, password: str) -> dict:
    response = await http.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password, "client_id": slug},
    )
    assert response.status_code == 200, response.text
    return response.json()


async def _onboard_verify_login(
    http: AsyncClient, fake_email: FakeEmailSender, *, slug: str, email: str
) -> dict:
    await _onboard(http, fake_email, slug=slug, email=email)
    await _verify_last_email(http, fake_email)
    return await _login(http, slug=slug, email=email, password=PASSWORD)


async def test_full_login_lifecycle(client):
    http, fake_email = client
    await _onboard(http, fake_email, slug="resto", email="owner@resto.com")
    assert fake_email.last().kind == "verification"

    # Login before verifying the email is rejected (only after correct password).
    response = await http.post(
        "/api/v1/auth/login",
        data={"username": "owner@resto.com", "password": PASSWORD, "client_id": "resto"},
    )
    assert response.status_code == 403
    assert response.json()["code"] == "email_not_verified"

    await _verify_last_email(http, fake_email)
    tokens = await _login(http, slug="resto", email="owner@resto.com", password=PASSWORD)

    # /ping echoes the tenant + role from the access token.
    ping = await http.get(
        "/api/v1/ping", headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    assert ping.status_code == 200
    assert ping.json()["role"] == "OWNER"

    # Refresh rotates: a new refresh token, and the old one stops working.
    rotated = await http.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert rotated.status_code == 200
    new_tokens = rotated.json()
    assert new_tokens["refresh_token"] != tokens["refresh_token"]

    reused = await http.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert reused.status_code == 401

    # Change password (revokes sessions), then log in with the new password.
    changed = await http.post(
        "/api/v1/auth/change-password",
        json={"current_password": PASSWORD, "new_password": "EvenB3tter!"},
        headers={"Authorization": f"Bearer {new_tokens['access_token']}"},
    )
    assert changed.status_code == 200
    await _login(http, slug="resto", email="owner@resto.com", password="EvenB3tter!")


async def test_wrong_password_is_invalid_credentials(client):
    http, fake_email = client
    await _onboard_verify_login(http, fake_email, slug="resto", email="owner@resto.com")
    response = await http.post(
        "/api/v1/auth/login",
        data={"username": "owner@resto.com", "password": "nope", "client_id": "resto"},
    )
    assert response.status_code == 401
    assert response.json()["code"] == "invalid_credentials"


async def test_ping_requires_token(client):
    http, _ = client
    assert (await http.get("/api/v1/ping")).status_code == 401


async def test_invite_rbac_and_accept(client):
    http, fake_email = client
    owner_tokens = await _onboard_verify_login(
        http, fake_email, slug="resto", email="owner@resto.com"
    )
    owner_auth = {"Authorization": f"Bearer {owner_tokens['access_token']}"}

    # OWNER invites a WAITER.
    invite = await http.post(
        "/api/v1/users/invite",
        json={"email": "waiter@resto.com", "role": "WAITER"},
        headers=owner_auth,
    )
    assert invite.status_code == 201, invite.text
    assert fake_email.last().kind == "invitation"
    invitation_token = _token_from_link(fake_email.last().link)

    accept = await http.post(
        "/api/v1/users/accept-invitation",
        json={"token": invitation_token, "password": "WaiterPass1!"},
    )
    assert accept.status_code == 200, accept.text

    waiter_tokens = await _login(
        http, slug="resto", email="waiter@resto.com", password="WaiterPass1!"
    )
    waiter_auth = {"Authorization": f"Bearer {waiter_tokens['access_token']}"}

    # A WAITER cannot invite — 403 insufficient_role.
    forbidden = await http.post(
        "/api/v1/users/invite",
        json={"email": "another@resto.com", "role": "KITCHEN"},
        headers=waiter_auth,
    )
    assert forbidden.status_code == 403
    assert forbidden.json()["code"] == "insufficient_role"


async def test_invite_cannot_grant_owner(client):
    http, fake_email = client
    owner_tokens = await _onboard_verify_login(
        http, fake_email, slug="resto", email="owner@resto.com"
    )
    response = await http.post(
        "/api/v1/users/invite",
        json={"email": "x@resto.com", "role": "OWNER"},
        headers={"Authorization": f"Bearer {owner_tokens['access_token']}"},
    )
    assert response.status_code == 422  # schema rejects OWNER invitations


async def test_forgot_and_reset_password(client):
    http, fake_email = client
    await _onboard_verify_login(http, fake_email, slug="resto", email="owner@resto.com")

    forgot = await http.post(
        "/api/v1/auth/forgot-password",
        json={"tenant_slug": "resto", "email": "owner@resto.com"},
    )
    assert forgot.status_code == 200
    assert fake_email.last().kind == "reset"
    reset_token = _token_from_link(fake_email.last().link)

    reset = await http.post(
        "/api/v1/auth/reset-password",
        json={"token": reset_token, "new_password": "Reset3dPass!"},
    )
    assert reset.status_code == 200
    await _login(http, slug="resto", email="owner@resto.com", password="Reset3dPass!")

    # Single-use: reusing the reset token fails.
    reused = await http.post(
        "/api/v1/auth/reset-password",
        json={"token": reset_token, "new_password": "Another1Pass!"},
    )
    assert reused.status_code == 409
    assert reused.json()["code"] == "token_already_used"


async def test_forgot_password_unknown_is_neutral(client):
    http, fake_email = client
    response = await http.post(
        "/api/v1/auth/forgot-password",
        json={"tenant_slug": "ghost", "email": "ghost@nowhere.com"},
    )
    assert response.status_code == 200
    assert fake_email.sent == []
