"""FCM adapter (Fase 4): sends push via the Firebase Cloud Messaging HTTP v1 API.

FCM delivers to iOS (through APNs) and Android with one integration. Auth is a
short-lived OAuth token minted from the project's service-account key (RS256 JWT →
token endpoint, standard flow) — done with PyJWT + httpx, no extra SDK. A send
never raises: a push failure must not break marking an order ready, so everything
is caught and logged; dead tokens (UNREGISTERED) are pruned.
"""

from __future__ import annotations

import json
import logging
import time

import httpx
import jwt

from app.domain.notification.ports import NotificationService, PushMessage
from app.domain.notification.repository import DeviceTokenRepository

logger = logging.getLogger("app.push")

_SCOPE = "https://www.googleapis.com/auth/firebase.messaging"
_TOKEN_URI = "https://oauth2.googleapis.com/token"
_SEND_URL = "https://fcm.googleapis.com/v1/projects/{project}/messages:send"


class FcmPushService(NotificationService):
    def __init__(
        self,
        device_tokens: DeviceTokenRepository,
        credentials_path: str,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._device_tokens = device_tokens
        self._credentials_path = credentials_path
        self._transport = transport
        self._sa: dict[str, str] | None = None
        self._access_token: str | None = None
        self._access_exp: float = 0.0

    def _service_account(self) -> dict[str, str]:
        if self._sa is None:
            with open(self._credentials_path, encoding="utf-8") as fh:
                self._sa = json.load(fh)
        return self._sa

    async def notify_user(
        self, *, tenant_id: str, user_id: str, message: PushMessage
    ) -> None:
        try:
            tokens = await self._device_tokens.list_for_user(tenant_id, user_id)
            if not tokens:
                return
            access = await self._access()
            sa = self._service_account()
            url = _SEND_URL.format(project=sa["project_id"])
            async with self._client() as client:
                for device in tokens:
                    await self._send_one(
                        client, url, access, device.token, message, tenant_id
                    )
        except Exception:  # noqa: BLE001 — un push nunca puede romper el flujo
            logger.warning("push notify failed (user=%s)", user_id, exc_info=True)

    async def _send_one(
        self,
        client: httpx.AsyncClient,
        url: str,
        access: str,
        token: str,
        message: PushMessage,
        tenant_id: str,
    ) -> None:
        resp = await client.post(
            url,
            headers={"Authorization": f"Bearer {access}"},
            json={
                "message": {
                    "token": token,
                    "notification": {"title": message.title, "body": message.body},
                    "data": message.data,
                }
            },
        )
        if resp.status_code == 404 or "UNREGISTERED" in resp.text:
            # Token muerto (desinstalada / rotó): lo sacamos para no reintentar.
            await self._device_tokens.delete(tenant_id, token)
        elif resp.status_code >= 400:
            logger.warning("fcm send %s: %s", resp.status_code, resp.text[:200])

    async def _access(self) -> str:
        """OAuth access token del service-account (RS256 JWT → token endpoint),
        cacheado hasta cerca de expirar."""
        now = time.time()
        if self._access_token is not None and now < self._access_exp - 60:
            return self._access_token
        sa = self._service_account()
        assertion = jwt.encode(
            {
                "iss": sa["client_email"],
                "scope": _SCOPE,
                "aud": sa.get("token_uri", _TOKEN_URI),
                "iat": int(now),
                "exp": int(now) + 3600,
            },
            sa["private_key"],
            algorithm="RS256",
        )
        async with self._client() as client:
            resp = await client.post(
                sa.get("token_uri", _TOKEN_URI),
                data={
                    "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                    "assertion": assertion,
                },
            )
            resp.raise_for_status()
            body = resp.json()
        self._access_token = body["access_token"]
        self._access_exp = now + int(body.get("expires_in", 3600))
        return self._access_token

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(transport=self._transport, timeout=10.0)
