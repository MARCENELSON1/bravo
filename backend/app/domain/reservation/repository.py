from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from app.domain.reservation.entities import Reservation
from app.domain.reservation.value_objects import ReservationStatus, ServiceTurn


class ReservationRepository(ABC):
    """Port for reservation persistence. Every method is scoped by ``tenant_id``."""

    @abstractmethod
    async def get_by_id(self, tenant_id: str, reservation_id: str) -> Reservation | None: ...

    @abstractmethod
    async def list(
        self,
        tenant_id: str,
        *,
        since: datetime | None = None,
        until: datetime | None = None,
        turn: ServiceTurn | None = None,
        status: ReservationStatus | None = None,
        table_id: str | None = None,
    ) -> list[Reservation]: ...

    @abstractmethod
    async def add(self, reservation: Reservation) -> None: ...

    @abstractmethod
    async def save(self, reservation: Reservation) -> None: ...
