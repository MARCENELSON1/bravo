"""Transporte de desarrollo: deja el lead en el log en vez de mandarlo al CRM.

Existe para poder levantar el backend sin credenciales de Twenty. La guarda de
settings lo rechaza en producción, justamente para que la landing real nunca
quede conectada a un destino que no guarda nada.
"""

from __future__ import annotations

import logging

from app.domain.marketing.entities import Lead
from app.domain.marketing.ports import LeadGateway

logger = logging.getLogger("app.marketing")


class LogLeadGateway(LeadGateway):
    async def submit(self, lead: Lead) -> None:
        logger.info(
            "[lead:log] email=%s nombre=%s mensaje=%s",
            lead.email,
            lead.name or "-",
            (lead.message or "-")[:200],
        )
