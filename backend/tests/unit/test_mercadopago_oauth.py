"""Unit tests for the MercadoPago OAuth client (in-process httpx transport)."""

from __future__ import annotations

import json

import httpx

from app.infrastructure.payments.mercadopago_oauth import MercadoPagoOAuthClient


def _client(handler) -> MercadoPagoOAuthClient:
    return MercadoPagoOAuthClient("CLIENT_ID", "SECRET", transport=httpx.MockTransport(handler))


def test_authorization_url() -> None:
    url = _client(lambda r: httpx.Response(200)).authorization_url(
        state="st4te", redirect_uri="https://app/cb"
    )
    assert url.startswith("https://auth.mercadopago.com.ar/authorization?")
    assert "client_id=CLIENT_ID" in url
    assert "state=st4te" in url
    assert "redirect_uri=https%3A%2F%2Fapp%2Fcb" in url
    assert "response_type=code" in url


async def test_exchange_code_parses_tokens() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/oauth/token"
        body = json.loads(request.content)
        assert body["grant_type"] == "authorization_code"
        assert body["code"] == "the-code"
        assert body["client_id"] == "CLIENT_ID"
        assert body["client_secret"] == "SECRET"
        return httpx.Response(
            200,
            json={
                "access_token": "AT",
                "refresh_token": "RT",
                "public_key": "PK",
                "user_id": 123456,
                "live_mode": False,
                "expires_in": 21600,
            },
        )

    tokens = await _client(handler).exchange_code(code="the-code", redirect_uri="https://app/cb")

    assert tokens.access_token == "AT"
    assert tokens.refresh_token == "RT"
    assert tokens.public_key == "PK"
    assert tokens.external_account_id == "123456"  # user_id stringified
    assert tokens.live_mode is False
    assert tokens.expires_in == 21600


async def test_refresh_uses_refresh_grant() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert body["grant_type"] == "refresh_token"
        assert body["refresh_token"] == "RT"
        return httpx.Response(
            200,
            json={"access_token": "AT2", "refresh_token": "RT2", "user_id": 7, "live_mode": True},
        )

    tokens = await _client(handler).refresh(refresh_token="RT")
    assert tokens.access_token == "AT2"
    assert tokens.live_mode is True


async def test_fetch_nickname() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/users/me"
        assert request.headers.get("Authorization") == "Bearer AT"
        return httpx.Response(200, json={"id": 1, "nickname": "MITIENDA"})

    assert await _client(handler).fetch_nickname(access_token="AT") == "MITIENDA"


async def test_fetch_nickname_never_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500)

    assert await _client(handler).fetch_nickname(access_token="AT") is None
