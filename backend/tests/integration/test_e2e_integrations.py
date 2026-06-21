"""End-to-end MercadoPago OAuth connect flow over HTTP + DB (provider faked).

connect → callback (signed state) → status connected → disconnect, with the
tokens encrypted at rest by a real Fernet cipher (overridden with a test key).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from urllib.parse import parse_qs, urlparse

import pytest_asyncio
from cryptography.fernet import Fernet
from dependency_injector import providers
from httpx import ASGITransport, AsyncClient

from app.domain.payment.ports import OAuthPaymentProvider, OAuthTokens
from app.infrastructure.security.fernet_cipher import FernetTokenCipher
from tests.fakes import FakeEmailSender
from tests.integration.test_e2e_auth import _onboard_verify_login
from tests.integration.test_e2e_payments import _auth


class FakeOAuth(OAuthPaymentProvider):
    def authorization_url(self, *, state: str, redirect_uri: str) -> str:
        return f"https://auth.test/mp?redirect_uri={redirect_uri}&state={state}"

    async def exchange_code(self, *, code: str, redirect_uri: str) -> OAuthTokens:
        return OAuthTokens(
            access_token="AT-seller",
            refresh_token="RT-seller",
            public_key="PK",
            external_account_id="seller-1",
            live_mode=False,
            expires_in=21600,
        )

    async def refresh(self, *, refresh_token: str) -> OAuthTokens:
        return await self.exchange_code(code="x", redirect_uri="x")

    async def fetch_nickname(self, *, access_token: str) -> str | None:
        return "MITIENDA"


@pytest_asyncio.fixture
async def int_client(clean_tables: None) -> AsyncIterator[tuple[AsyncClient, FakeEmailSender]]:
    from app.main import create_app

    app = create_app()
    container = app.state.container
    fake_email = FakeEmailSender()
    container.email_sender.override(providers.Object(fake_email))
    container.mercadopago_oauth.override(providers.Object(FakeOAuth()))
    container.token_cipher.override(
        providers.Object(FernetTokenCipher(Fernet.generate_key().decode()))
    )
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="https://test") as http:
            yield http, fake_email
    finally:
        container.email_sender.reset_override()
        container.mercadopago_oauth.reset_override()
        container.token_cipher.reset_override()
        await container.db().dispose()


async def test_connect_callback_status_disconnect(int_client) -> None:
    http, fake_email = int_client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    h = _auth(tokens)

    # 1. connect → authorize URL with a signed state
    connect = await http.get("/api/v1/integrations/mercadopago/connect", headers=h)
    assert connect.status_code == 200, connect.text
    state = parse_qs(urlparse(connect.json()["url"]).query)["state"][0]

    # 2. callback (public, trusted via state) → redirect ok + credential stored
    cb = await http.get(
        f"/api/v1/integrations/mercadopago/callback?code=abc&state={state}",
        follow_redirects=False,
    )
    assert cb.status_code == 302
    assert "mp=ok" in cb.headers["location"]

    # 3. status → connected, with the seller's account + nickname
    st = await http.get("/api/v1/integrations/mercadopago", headers=h)
    assert st.status_code == 200
    assert st.json() == {
        "connected": True,
        "nickname": "MITIENDA",
        "external_account_id": "seller-1",
        "live_mode": False,
    }

    # 4. disconnect → status back to not connected
    assert (await http.delete("/api/v1/integrations/mercadopago", headers=h)).status_code == 204
    final = await http.get("/api/v1/integrations/mercadopago", headers=h)
    assert final.json()["connected"] is False


async def test_callback_rejects_tampered_state(int_client) -> None:
    http, fake_email = int_client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    h = _auth(tokens)

    cb = await http.get(
        "/api/v1/integrations/mercadopago/callback?code=abc&state=forged.signature",
        follow_redirects=False,
    )
    assert cb.status_code == 302
    assert "mp=error" in cb.headers["location"]
    final = await http.get("/api/v1/integrations/mercadopago", headers=h)
    assert final.json()["connected"] is False
