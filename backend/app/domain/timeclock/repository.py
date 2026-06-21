from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from app.domain.timeclock.entities import Shift


class ShiftRepository(ABC):
    """Port for shift persistence. Every method is scoped by ``tenant_id``."""

    @abstractmethod
    async def get_open_for_user(self, tenant_id: str, user_id: str) -> Shift | None: ...

    @abstractmethod
    async def get_by_id(self, tenant_id: str, shift_id: str) -> Shift | None: ...

    @abstractmethod
    async def list(
        self,
        tenant_id: str,
        *,
        user_id: str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> list[Shift]: ...

    @abstractmethod
    async def add(self, shift: Shift) -> None: ...

    @abstractmethod
    async def save(self, shift: Shift) -> None: ...
