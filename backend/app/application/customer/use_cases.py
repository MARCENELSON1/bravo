from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4

from app.domain.customer.entities import Customer
from app.domain.customer.exceptions import CustomerNotFound
from app.domain.customer.repository import CustomerRepository
from app.domain.identity.ports import TenantContext
from app.domain.order.exceptions import OrderNotFound
from app.domain.order.repository import OrderRepository


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


class AssignOrderCustomer:
    """Attribute (or clear) the customer of an order, so their purchase history
    accrues. ``customer_id=None`` clears it. Honest: only explicitly-attributed
    orders count for a customer — nothing is inferred."""

    def __init__(
        self,
        orders: OrderRepository,
        customers: CustomerRepository,
        tenant_context: TenantContext,
    ) -> None:
        self._orders = orders
        self._customers = customers
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str, order_id: str, customer_id: str | None):
        self._tenant_context.set(tenant_id)
        order = await self._orders.get_by_id(tenant_id, order_id)
        if order is None:
            raise OrderNotFound()
        if customer_id is not None:
            customer = await self._customers.get_by_id(tenant_id, customer_id)
            if customer is None:
                raise CustomerNotFound()
        order.customer_id = customer_id
        await self._orders.save(order)
        return order


@dataclass(frozen=True)
class CustomerHistory:
    """What a customer has spent with us, only over explicitly-attributed PAID
    orders (nothing inferred). ``visits`` = distinct attributed orders."""

    customer_id: str
    currency: str
    visits: int
    total_spent: int  # minor units
    last_visit_at: datetime | None


class CustomerHistoryReadModel(ABC):
    """Aggregates a customer's attributed sales. Scoped by ``tenant_id`` (RLS +
    explicit filter); read-only."""

    @abstractmethod
    async def history(self, tenant_id: str, customer_id: str) -> CustomerHistory: ...


class GetCustomerHistory:
    def __init__(
        self,
        customers: CustomerRepository,
        read_model: CustomerHistoryReadModel,
        tenant_context: TenantContext,
    ) -> None:
        self._customers = customers
        self._read_model = read_model
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str, customer_id: str) -> CustomerHistory:
        self._tenant_context.set(tenant_id)
        if await self._customers.get_by_id(tenant_id, customer_id) is None:
            raise CustomerNotFound()
        return await self._read_model.history(tenant_id, customer_id)
