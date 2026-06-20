from __future__ import annotations

from uuid import uuid4

from app.domain.identity.ports import TenantContext
from app.domain.order.entities import Order
from app.domain.order.exceptions import OrderNotFound
from app.domain.order.repository import OrderRepository
from app.domain.order.value_objects import OrderStatus
from app.domain.payment.entities import Payment
from app.domain.payment.exceptions import InvalidPaymentAmount
from app.domain.payment.ports import PaymentGateway
from app.domain.payment.repository import PaymentRepository
from app.domain.payment.value_objects import PaymentDirection, PaymentMethod, PaymentStatus
from app.domain.shared.money import Money
from app.domain.tenant.exceptions import TenantNotFound
from app.domain.tenant.repository import TenantRepository


class RegisterPayment:
    """Cobro (INFLOW) de una comanda. Concilia: si los INFLOW confirmados
    cubren el total, la comanda pasa a PAID."""

    def __init__(
        self,
        payments: PaymentRepository,
        orders: OrderRepository,
        gateway: PaymentGateway,
        tenant_context: TenantContext,
    ) -> None:
        self._payments = payments
        self._orders = orders
        self._gateway = gateway
        self._tenant_context = tenant_context

    async def execute(
        self, *, tenant_id: str, order_id: str, method: str, amount: int
    ) -> Payment:
        self._tenant_context.set(tenant_id)
        if amount <= 0:
            raise InvalidPaymentAmount()
        order = await self._orders.get_by_id(tenant_id, order_id)
        if order is None:
            raise OrderNotFound()
        payment = Payment(
            id=str(uuid4()),
            tenant_id=tenant_id,
            direction=PaymentDirection.INFLOW,
            amount=Money(amount, order.currency),
            method=PaymentMethod(method),
            status=PaymentStatus.PENDING,
            order_id=order_id,
        )
        payment = await self._gateway.charge(payment=payment)
        await self._payments.add(payment)
        await self._reconcile(tenant_id, order)
        return payment

    async def _reconcile(self, tenant_id: str, order: Order) -> None:
        payments = await self._payments.list_by_order(tenant_id, order.id)
        paid = sum(
            p.amount.amount
            for p in payments
            if p.direction is PaymentDirection.INFLOW and p.status is PaymentStatus.CONFIRMED
        )
        if paid >= order.total().amount and order.status is not OrderStatus.PAID:
            order.mark_paid()
            await self._orders.save(order)


class RegisterExpense:
    """Egreso (OUTFLOW): gasto / pago saliente, sin comanda asociada."""

    def __init__(
        self,
        payments: PaymentRepository,
        tenants: TenantRepository,
        gateway: PaymentGateway,
        tenant_context: TenantContext,
    ) -> None:
        self._payments = payments
        self._tenants = tenants
        self._gateway = gateway
        self._tenant_context = tenant_context

    async def execute(
        self,
        *,
        tenant_id: str,
        method: str,
        amount: int,
        category: str | None,
        counterparty: str | None,
        description: str | None,
    ) -> Payment:
        self._tenant_context.set(tenant_id)
        if amount <= 0:
            raise InvalidPaymentAmount()
        tenant = await self._tenants.get_by_id(tenant_id)
        if tenant is None:
            raise TenantNotFound()
        payment = Payment(
            id=str(uuid4()),
            tenant_id=tenant_id,
            direction=PaymentDirection.OUTFLOW,
            amount=Money(amount, tenant.currency),
            method=PaymentMethod(method),
            status=PaymentStatus.PENDING,
            category=category,
            counterparty=counterparty,
            description=description,
        )
        payment = await self._gateway.charge(payment=payment)
        await self._payments.add(payment)
        return payment


class ListOrderPayments:
    def __init__(self, payments: PaymentRepository, tenant_context: TenantContext) -> None:
        self._payments = payments
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str, order_id: str) -> list[Payment]:
        self._tenant_context.set(tenant_id)
        return await self._payments.list_by_order(tenant_id, order_id)


class ListExpenses:
    def __init__(self, payments: PaymentRepository, tenant_context: TenantContext) -> None:
        self._payments = payments
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str) -> list[Payment]:
        self._tenant_context.set(tenant_id)
        return await self._payments.list_expenses(tenant_id)
