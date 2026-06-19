from __future__ import annotations

from email.message import EmailMessage

import aiosmtplib

from app.domain.identity.ports import EmailSender
from app.infrastructure.email.templates import (
    invitation_email,
    password_reset_email,
    verification_email,
)


class SmtpEmailSender(EmailSender):
    """Sends email via SMTP (aiosmtplib, optional STARTTLS). Credentials come from
    settings and are never logged."""

    def __init__(
        self,
        host: str,
        port: int,
        username: str | None,
        password: str | None,
        from_email: str,
        use_tls: bool,
    ) -> None:
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._from_email = from_email
        self._use_tls = use_tls

    async def _send(self, to: str, subject: str, body: str) -> None:
        message = EmailMessage()
        message["From"] = self._from_email
        message["To"] = to
        message["Subject"] = subject
        message.set_content(body)
        await aiosmtplib.send(
            message,
            hostname=self._host,
            port=self._port,
            username=self._username or None,
            password=self._password or None,
            start_tls=self._use_tls,
        )

    async def send_email_verification(self, *, to: str, link: str) -> None:
        subject, body = verification_email(link)
        await self._send(to, subject, body)

    async def send_password_reset(self, *, to: str, link: str) -> None:
        subject, body = password_reset_email(link)
        await self._send(to, subject, body)

    async def send_invitation(self, *, to: str, link: str, tenant_name: str) -> None:
        subject, body = invitation_email(link, tenant_name)
        await self._send(to, subject, body)
