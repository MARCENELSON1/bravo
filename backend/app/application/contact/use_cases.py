from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import uuid4

from app.application.clock import utcnow
from app.domain.contact.entities import ContactLog
from app.domain.contact.repository import ContactLogRepository
from app.domain.customer.exceptions import CustomerNotFound
from app.domain.customer.repository import CustomerRepository
from app.domain.identity.ports import TenantContext


class LogContact:
    """Registrar que se contactó a un cliente (tras escribirle por WhatsApp)."""

    def __init__(
        self,
        contacts: ContactLogRepository,
        customers: CustomerRepository,
        tenant_context: TenantContext,
    ) -> None:
        self._contacts = contacts
        self._customers = customers
        self._tenant_context = tenant_context

    async def execute(
        self,
        *,
        tenant_id: str,
        customer_id: str,
        contacted_by: str,
        reason: str = "manual",
    ) -> ContactLog:
        self._tenant_context.set(tenant_id)
        if await self._customers.get_by_id(tenant_id, customer_id) is None:
            raise CustomerNotFound()
        log = ContactLog(
            id=str(uuid4()),
            tenant_id=tenant_id,
            customer_id=customer_id,
            reason=reason,
            contacted_by=contacted_by,
            contacted_at=utcnow(),
        )
        await self._contacts.add(log)
        return log


class GetRecentContacts:
    """Los clientes contactados en los últimos ``days`` días (para no re-sugerir)."""

    def __init__(
        self, contacts: ContactLogRepository, tenant_context: TenantContext
    ) -> None:
        self._contacts = contacts
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str, days: int = 7) -> list[str]:
        self._tenant_context.set(tenant_id)
        since = utcnow() - timedelta(days=max(days, 0))
        return await self._contacts.recent_customer_ids(tenant_id, since=since)


@dataclass(frozen=True)
class ContactResult:
    """El loop de resultado: de los contactados en la ventana, cuántos volvieron
    (tuvieron una visita atribuida DESPUÉS del contacto) y cuánto gastaron."""

    currency: str
    contacted: int
    returned: int
    revenue: int  # minor units, gasto post-contacto


class ContactResultReadModel(ABC):
    @abstractmethod
    async def result(self, tenant_id: str, *, since: datetime) -> ContactResult: ...


class GetContactResult:
    def __init__(
        self, read_model: ContactResultReadModel, tenant_context: TenantContext
    ) -> None:
        self._read_model = read_model
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str, days: int = 30) -> ContactResult:
        self._tenant_context.set(tenant_id)
        since = utcnow() - timedelta(days=max(days, 1))
        return await self._read_model.result(tenant_id, since=since)
