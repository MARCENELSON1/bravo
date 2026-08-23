from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from app.domain.contact.entities import ContactLog


class ContactLogRepository(ABC):
    """Port for the contact log. Every method is scoped by ``tenant_id``."""

    @abstractmethod
    async def add(self, log: ContactLog) -> None: ...

    @abstractmethod
    async def recent_customer_ids(
        self, tenant_id: str, *, since: datetime
    ) -> list[str]:
        """Distinct customer ids contacted since ``since`` (para no re-sugerir)."""
        ...
