"""Resend adapter: sends transactional email through the Resend HTTP API.

Preferred over SMTP in a container deploy: no long-lived socket to a mail
server, errors arrive as structured JSON, and every send returns Resend's
message id (useful when chasing a delivery in their dashboard).

The copy lives in ``templates.py`` and is shared with the other transports, so
switching EMAIL_TRANSPORT never changes what the user reads. The API key is
kept in memory only and never logged.
"""

from __future__ import annotations

import logging

import httpx

from app.domain.identity.ports import EmailSender
from app.infrastructure.email.templates import (
    invitation_email,
    password_reset_email,
    verification_email,
)

logger = logging.getLogger("app.email")

_API_BASE = "https://api.resend.com"


class ResendEmailSendFailed(RuntimeError):
    """Resend rejected the send. Carries the status and Resend's own message."""


class ResendEmailSender(EmailSender):
    def __init__(
        self,
        api_key: str,
        from_email: str,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._api_key = api_key
        self._from_email = from_email
        self._transport = transport

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=_API_BASE,
            transport=self._transport,
            headers={"Authorization": f"Bearer {self._api_key}"},
            timeout=10.0,
        )

    async def _send(self, to: str, subject: str, body: str) -> None:
        async with self._client() as client:
            response = await client.post(
                "/emails",
                json={
                    "from": self._from_email,
                    "to": [to],
                    "subject": subject,
                    "text": body,
                },
            )
        if response.status_code >= 400:
            # Resend answers errors as {"statusCode":..,"name":..,"message":..}.
            detail = ""
            try:
                detail = str(response.json().get("message") or "")
            except ValueError:
                detail = response.text[:200]
            raise ResendEmailSendFailed(f"resend returned {response.status_code}: {detail}")
        message_id = ""
        try:
            message_id = str(response.json().get("id") or "")
        except ValueError:
            pass
        logger.info("[email:sent] to=%s subject=%s resend_id=%s", to, subject, message_id)

    async def send_email_verification(self, *, to: str, link: str) -> None:
        subject, body = verification_email(link)
        await self._send(to, subject, body)

    async def send_password_reset(self, *, to: str, link: str) -> None:
        subject, body = password_reset_email(link)
        await self._send(to, subject, body)

    async def send_invitation(self, *, to: str, link: str, tenant_name: str) -> None:
        subject, body = invitation_email(link, tenant_name)
        await self._send(to, subject, body)
