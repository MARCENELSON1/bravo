from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.marketing.entities import Lead


class LeadGateway(ABC):
    """Destino de los leads de la landing (CRM). Implementarlo NO debe tragarse
    los fallos: si el lead no llegó, tiene que propagar el error."""

    @abstractmethod
    async def submit(self, lead: Lead) -> None: ...
