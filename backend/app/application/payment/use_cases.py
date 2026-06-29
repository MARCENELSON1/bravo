from __future__ import annotations

from uuid import uuid4

from app.application.analytics.ports import SalesProjector
from app.application.inventory.ports import InventoryConsumer
from app.domain.identity.ports import TenantContext
from app.domain.order.exceptions import OrderNotFound
from app.domain.order.repository import OrderRepository
from app.domain.order.value_objects import OrderStatus
from app.domain.payment.entities import Payment
from app.domain.payment.exceptions import (
    InvalidPaymentAmount,
    InvalidWebhookSignature,
    PaymentNotFound,
)
from app.domain.payment.ports import (
    PaymentCredentialsResolver,
    PaymentGateway,
    PaymentNotificationGateway,
)
from app.domain.payment.repository import PaymentRepository
from app.domain.payment.value_objects import PaymentDirection, PaymentMethod, PaymentStatus
from app.domain.shared.money import Money
from app.domain.tenant.exceptions import TenantNotFound
from app.domain.tenant.repository import TenantRepository


async def _settle_order(
    payments: PaymentRepository,
    orders: OrderRepository,
    tenant_id: str,
    order_id: str,
    inventory: InventoryConsumer | None = None,
    sales: SalesProjector | None = None,
) -> None:
    """Mark the order PAID once confirmed INFLOW payments cover its total.

    On the PAID transition, fire the optional post-paid collaborators (both
    idempotent, both behind a port, neither blocks the cobro): discount the
    recipe's stock (``inventory``) and project the canonical sale facts (``sales``).
    """
    order = await orders.get_by_id(tenant_id, order_id)
    if order is None:
        return
    confirmed = await payments.list_by_order(tenant_id, order_id)
    paid = sum(
        p.amount.amount
        for p in confirmed
        if p.direction is PaymentDirection.INFLOW and p.status is PaymentStatus.CONFIRMED
    )
    if paid >= order.total().amount and order.status is not OrderStatus.PAID:
        order.mark_paid()
        await orders.save(order)
        if inventory is not None:
            await inventory.consume_for_order(tenant_id, order_id)
        if sales is not None:
            await sales.project_order(tenant_id, order_id)


class RegisterPayment:
    """Cobro (INFLOW) de una comanda. Concilia: si los INFLOW confirmados
    cubren el total, la comanda pasa a PAID."""

    def __init__(
        self,
        payments: PaymentRepository,
        orders: OrderRepository,
        gateway: PaymentGateway,
        tenant_context: TenantContext,
        inventory: InventoryConsumer | None = None,
        sales: SalesProjector | None = None,
    ) -> None:
        self._payments = payments
        self._orders = orders
        self._gateway = gateway
        self._tenant_context = tenant_context
        self._inventory = inventory
        self._sales = sales

    async def execute(
        self, *, tenant_id: str, order_id: str, method: str, amount: int, tip: int = 0
    ) -> Payment:
        self._tenant_context.set(tenant_id)
        if amount <= 0 or tip < 0:
            raise InvalidPaymentAmount()
        order = await self._orders.get_by_id(tenant_id, order_id)
        if order is None:
            raise OrderNotFound()
        # The tip rides on top of the sale ``amount`` — it does NOT count toward
        # covering the order total (settle only looks at ``amount``).
        payment = Payment(
            id=str(uuid4()),
            tenant_id=tenant_id,
            direction=PaymentDirection.INFLOW,
            amount=Money(amount, order.currency),
            method=PaymentMethod(method),
            status=PaymentStatus.PENDING,
            order_id=order_id,
            tip_amount=tip,
        )
        payment = await self._gateway.charge(payment=payment)
        await self._payments.add(payment)
        await _settle_order(
            self._payments, self._orders, tenant_id, order.id, self._inventory, self._sales
        )
        return payment


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


class RefundPayment:
    """Anular/reembolsar un cobro confirmado (money-only). El pago pasa a REFUNDED
    y deja de contar en el arqueo; la proyección de venta no se toca (deshacer la
    venta es el flujo de reabrir, aparte)."""

    def __init__(self, payments: PaymentRepository, tenant_context: TenantContext) -> None:
        self._payments = payments
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str, payment_id: str) -> Payment:
        self._tenant_context.set(tenant_id)
        payment = await self._payments.get_by_id(tenant_id, payment_id)
        if payment is None:
            raise PaymentNotFound()
        payment.refund()
        await self._payments.save(payment)
        return payment


class ListExpenses:
    def __init__(self, payments: PaymentRepository, tenant_context: TenantContext) -> None:
        self._payments = payments
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str) -> list[Payment]:
        self._tenant_context.set(tenant_id)
        return await self._payments.list_expenses(tenant_id)


class ConfirmGatewayPayment:
    """Handle an inbound gateway notification (webhook).

    The endpoint is public and carries no user token, so this:
      1. authenticates the request via the gateway signature;
      2. asks the gateway for the authoritative status (never trusts the body);
      3. routes to the tenant/payment via the ``external_reference`` we set when
         charging (``"<tenant_id>:<payment_id>"``);
      4. confirms (or fails) the payment idempotently and settles its order.
    """

    def __init__(
        self,
        payments: PaymentRepository,
        orders: OrderRepository,
        notifications: PaymentNotificationGateway,
        resolver: PaymentCredentialsResolver,
        tenant_context: TenantContext,
        inventory: InventoryConsumer | None = None,
        sales: SalesProjector | None = None,
    ) -> None:
        self._payments = payments
        self._orders = orders
        self._notifications = notifications
        self._resolver = resolver
        self._tenant_context = tenant_context
        self._inventory = inventory
        self._sales = sales

    async def execute(
        self,
        *,
        data_id: str | None,
        request_id: str | None,
        ts: str | None,
        received_hmac: str,
        account_id: str | None = None,
    ) -> None:
        if not self._notifications.verify_signature(
            data_id=data_id, request_id=request_id, ts=ts, received_hmac=received_hmac
        ):
            raise InvalidWebhookSignature()
        if data_id is None:
            return
        # Resolve the seller's token (multi-tenant); falls back inside the gateway
        # to the app-level token when the account can't be mapped.
        access_token = await self._resolve_seller_token(account_id)
        status = await self._notifications.fetch_status(
            gateway_payment_id=data_id, access_token=access_token
        )
        ref = status.external_reference
        if not ref or ":" not in ref:
            return  # not one of ours — ignore quietly
        tenant_id, payment_id = ref.split(":", 1)
        self._tenant_context.set(tenant_id)
        payment = await self._payments.get_by_id(tenant_id, payment_id)
        if payment is None or payment.status is PaymentStatus.CONFIRMED:
            return  # unknown or already settled → idempotent no-op
        if status.status is PaymentStatus.CONFIRMED:
            payment.confirm()
            payment.external_ref = status.gateway_payment_id
            await self._payments.save(payment)
            if payment.order_id is not None:
                await _settle_order(
                    self._payments,
                    self._orders,
                    tenant_id,
                    payment.order_id,
                    self._inventory,
                    self._sales,
                )
        elif status.status is PaymentStatus.FAILED:
            payment.fail()
            payment.external_ref = status.gateway_payment_id
            await self._payments.save(payment)

    async def _resolve_seller_token(self, account_id: str | None) -> str | None:
        """Map the provider seller id (from the notification) to the tenant's
        token. Best-effort: on any miss the gateway uses its app-level token."""
        if not account_id:
            return None
        try:
            tenant_id = await self._resolver.tenant_for_account(account_id)
            if tenant_id is None:
                return None
            return (await self._resolver.for_tenant(tenant_id)).access_token
        except Exception:
            return None
