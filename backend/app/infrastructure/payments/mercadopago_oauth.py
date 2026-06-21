"""MercadoPago OAuth client (Fase 3.5): the 'Conectar con MercadoPago' flow.

Endpoints per MercadoPago's OAuth docs (verify against the panel at live-test):
  * authorize:  GET  https://auth.mercadopago.com.ar/authorization
  * token:      POST https://api.mercadopago.com/oauth/token  (code & refresh)
  * user info:  GET  https://api.mercadopago.com/users/me
The token response already carries user_id / public_key / live_mode / expires_in.
Client id/secret are app-level (NÚCLEO's MP application), from the environment.
"""

from __future__ import annotations

from urllib.parse import urlencode

import httpx

from app.domain.payment.ports import OAuthPaymentProvider, OAuthTokens

_AUTH_URL = "https://auth.mercadopago.com.ar/authorization"
_API_BASE = "https://api.mercadopago.com"


class MercadoPagoOAuthClient(OAuthPaymentProvider):
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._transport = transport

    def authorization_url(self, *, state: str, redirect_uri: str) -> str:
        params = urlencode(
            {
                "client_id": self._client_id,
                "response_type": "code",
                "platform_id": "mp",
                "state": state,
                "redirect_uri": redirect_uri,
            }
        )
        return f"{_AUTH_URL}?{params}"

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(base_url=_API_BASE, transport=self._transport, timeout=10.0)

    async def _token(self, body: dict[str, str]) -> OAuthTokens:
        body = {"client_id": self._client_id, "client_secret": self._client_secret, **body}
        async with self._client() as client:
            resp = await client.post("/oauth/token", json=body)
            resp.raise_for_status()
            data = resp.json()
        return OAuthTokens(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            public_key=data.get("public_key"),
            external_account_id=str(data["user_id"]),
            live_mode=bool(data.get("live_mode", False)),
            expires_in=data.get("expires_in"),
        )

    async def exchange_code(self, *, code: str, redirect_uri: str) -> OAuthTokens:
        return await self._token(
            {"grant_type": "authorization_code", "code": code, "redirect_uri": redirect_uri}
        )

    async def refresh(self, *, refresh_token: str) -> OAuthTokens:
        return await self._token({"grant_type": "refresh_token", "refresh_token": refresh_token})

    async def fetch_nickname(self, *, access_token: str) -> str | None:
        try:
            async with self._client() as client:
                resp = await client.get(
                    "/users/me", headers={"Authorization": f"Bearer {access_token}"}
                )
                resp.raise_for_status()
                return resp.json().get("nickname")
        except Exception:
            return None  # nickname is cosmetic; never fail the connection over it
