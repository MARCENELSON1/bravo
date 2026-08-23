from __future__ import annotations

from uuid import uuid4

from app.domain.customer.entities import Customer
from app.domain.customer.exceptions import CustomerNotFound
from app.domain.customer.repository import CustomerRepository
from app.domain.identity.ports import TenantContext


def _norm_phone(phone: str | None) -> str | None:
    """Keep only digits so a ``wa.me/<phone>`` link works. Empty → None."""
    if phone is None:
        return None
    digits = "".join(c for c in phone if c.isdigit())
    return digits or None


def _clean(text: str | None) -> str | None:
    if text is None:
        return None
    stripped = text.strip()
    return stripped or None


class ListCustomers:
    def __init__(
        self, customers: CustomerRepository, tenant_context: TenantContext
    ) -> None:
        self._customers = customers
        self._tenant_context = tenant_context

    async def execute(
        self, *, tenant_id: str, search: str | None = None
    ) -> list[Customer]:
        self._tenant_context.set(tenant_id)
        return await self._customers.list(tenant_id, search=search)


class GetCustomer:
    def __init__(
        self, customers: CustomerRepository, tenant_context: TenantContext
    ) -> None:
        self._customers = customers
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str, customer_id: str) -> Customer:
        self._tenant_context.set(tenant_id)
        customer = await self._customers.get_by_id(tenant_id, customer_id)
        if customer is None:
            raise CustomerNotFound()
        return customer


class CreateCustomer:
    def __init__(
        self, customers: CustomerRepository, tenant_context: TenantContext
    ) -> None:
        self._customers = customers
        self._tenant_context = tenant_context

    async def execute(
        self,
        *,
        tenant_id: str,
        name: str,
        phone: str | None = None,
        email: str | None = None,
        notes: str | None = None,
        no_contactar: bool = False,
    ) -> Customer:
        self._tenant_context.set(tenant_id)
        customer = Customer(
            id=str(uuid4()),
            tenant_id=tenant_id,
            name=name.strip(),
            phone=_norm_phone(phone),
            email=_clean(email),
            notes=_clean(notes),
            no_contactar=no_contactar,
        )
        await self._customers.add(customer)
        return customer


class UpdateCustomer:
    def __init__(
        self, customers: CustomerRepository, tenant_context: TenantContext
    ) -> None:
        self._customers = customers
        self._tenant_context = tenant_context

    async def execute(
        self,
        *,
        tenant_id: str,
        customer_id: str,
        name: str,
        phone: str | None,
        email: str | None,
        notes: str | None,
        no_contactar: bool,
    ) -> Customer:
        self._tenant_context.set(tenant_id)
        customer = await self._customers.get_by_id(tenant_id, customer_id)
        if customer is None:
            raise CustomerNotFound()
        customer.name = name.strip()
        customer.phone = _norm_phone(phone)
        customer.email = _clean(email)
        customer.notes = _clean(notes)
        customer.no_contactar = no_contactar
        await self._customers.save(customer)
        return customer


class DeleteCustomer:
    def __init__(
        self, customers: CustomerRepository, tenant_context: TenantContext
    ) -> None:
        self._customers = customers
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str, customer_id: str) -> None:
        self._tenant_context.set(tenant_id)
        customer = await self._customers.get_by_id(tenant_id, customer_id)
        if customer is None:
            raise CustomerNotFound()
        await self._customers.delete(tenant_id, customer_id)
