from __future__ import annotations

import logging

from app.domain.identity.ports import EmailSender

logger = logging.getLogger("app.email")


class ConsoleEmailSender(EmailSender):
    """Dev transport: logs the link instead of sending (no SMTP server needed)."""

    async def send_email_verification(self, *, to: str, link: str) -> None:
        logger.info("[email:verification] to=%s link=%s", to, link)

    async def send_password_reset(self, *, to: str, link: str) -> None:
        logger.info("[email:reset] to=%s link=%s", to, link)

    async def send_invitation(self, *, to: str, link: str, tenant_name: str) -> None:
        logger.info("[email:invitation] to=%s tenant=%s link=%s", to, tenant_name, link)
