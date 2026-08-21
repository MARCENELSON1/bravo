"""Caso de uso: registrar un lead de la landing."""

from __future__ import annotations

import re

from app.domain.marketing.entities import Lead
from app.domain.marketing.exceptions import InvalidLead
from app.domain.marketing.ports import LeadGateway

_EMAIL = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
_MAX_MESSAGE = 2000
_MAX_NAME = 200


class SubmitLead:
    def __init__(self, gateway: LeadGateway) -> None:
        self._gateway = gateway

    async def execute(self, *, email: str, name: str | None, message: str | None) -> None:
        clean_email = (email or "").strip()
        if not _EMAIL.match(clean_email):
            raise InvalidLead()
        await self._gateway.submit(
            Lead(
                email=clean_email,
                name=_trim(name, _MAX_NAME),
                message=_trim(message, _MAX_MESSAGE),
            )
        )


def _trim(value: str | None, limit: int) -> str | None:
    """El endpoint es público: se recorta lo que entra antes de mandarlo al CRM."""
    if value is None:
        return None
    stripped = value.strip()
    return stripped[:limit] or None
