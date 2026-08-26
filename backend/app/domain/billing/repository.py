from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.billing.entities import Plan, Subscription
from app.domain.billing.value_objects import BillingRegion


class PlanRepository(ABC):
    """Catálogo de planes. Read-only (los planes son data de configuración)."""

    @abstractmethod
    async def list_active(self, region: BillingRegion) -> list[Plan]:
        """Planes activos de una región (lo que se muestra en el pricing)."""

    @abstractmethod
    async def get_by_id(self, plan_id: str) -> Plan | None: ...


class SubscriptionRepository(ABC):
    """Una suscripción por tenant. Tenant-scoped."""

    @abstractmethod
    async def get_by_tenant(self, tenant_id: str) -> Subscription | None: ...

    @abstractmethod
    async def get_by_external_ref(self, external_ref: str) -> Subscription | None:
        """Resuelve la suscripción desde el id de la pasarela (para webhooks)."""

    @abstractmethod
    async def add(self, subscription: Subscription) -> None: ...

    @abstractmethod
    async def save(self, subscription: Subscription) -> None: ...
