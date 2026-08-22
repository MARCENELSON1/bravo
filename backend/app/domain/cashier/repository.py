from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.cashier.entities import CashMovement, CashSession


class CashSessionRepository(ABC):
    """Port for register-session persistence. Scoped by ``tenant_id``."""

    @abstractmethod
    async def get_by_id(self, tenant_id: str, session_id: str) -> CashSession | None: ...

    @abstractmethod
    async def get_open(self, tenant_id: str) -> CashSession | None:
        """The currently OPEN session for the tenant, if any (one at a time)."""

    @abstractmethod
    async def add(self, session: CashSession) -> None: ...

    @abstractmethod
    async def save(self, session: CashSession) -> None: ...


class CashMovementRepository(ABC):
    """Port for manual cash-drawer movements. Scoped by ``tenant_id``."""

    @abstractmethod
    async def add(self, movement: CashMovement) -> None: ...

    @abstractmethod
    async def list_for_session(
        self, tenant_id: str, cash_session_id: str
    ) -> list[CashMovement]:
        """All movements of a session, oldest first."""
