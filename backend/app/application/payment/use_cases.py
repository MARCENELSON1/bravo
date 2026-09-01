from __future__ import annotations

import logging
from uuid import uuid4

from app.application.analytics.ports import SalesProjector
from app.application.inventory.ports import InventoryConsumer
from app.application.tax.reporting import TaxReportLedger
from app.domain.cashier.exceptions import NoOpenCashSession
from app.domain.cashier.policy import CashSessionPolicy
from app.domain.cashier.repository import CashSessionRepository
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
from app.domain.payment.fees import fee_of
from app.domain.payment.ports import (
    PaymentCredentialsResolver,
    PaymentGateway,
    PaymentNotificationGateway,
)
from app.domain.payment.repository import PaymentFeeRateRepository, PaymentRepository
from app.domain.payment.value_objects import PaymentDirection, PaymentMethod, PaymentStatus
from app.domain.shared.money import Money
from app.domain.tenant.exceptions import TenantNotFound
from app.domain.tenant.repository import TenantRepository

logger = logging.getLogger(__name__)


async def _settle_order(
    payments: PaymentRepository,
    orders: OrderRepository,
    tenant_id: str,
    order_id: str,
    inventory: InventoryConsumer | None = None,
    sales: SalesProjector | None = None,
    tax_outbox: TaxReportLedger | None = None,
) -> None:
    """Mark the order PAID once confirmed INFLOW payments cover its total.

    On the PAID transition, fire the optional post-paid collaborators (all
    idempotent, all behind a port, none blocks the cobro): discount the recipe's
    stock (``inventory``), project the canonical sale facts (``sales``), and — only
    if any sales tax was actually collected — enqueue the sale to report to the
    tax provider (``tax_outbox``). The ``tax > 0`` gate keeps AR untouched: it
    never collects tax, so nothing is ever enqueued (perfect parity).
    """
    order = await orders.get_by_id(tenant_id, order_id)
    if order is None:
        return
    confirmed = await payments.list_by_order(tenant_id, order_id)
    inflow_confirmed = [
        p
        for p in confirmed
        if p.direction is PaymentDirection.INFLOW and p.status is PaymentStatus.CONFIRMED
    ]
    paid = sum(p.amount.amount for p in inflow_confirmed)
    if paid >= order.total().amount and order.status is not OrderStatus.PAID:
        order.mark_paid()
        await orders.save(order)
        if inventory is not None:
            await inventory.consume_for_order(tenant_id, order_id)
        if sales is not None:
            await sales.project_order(tenant_id, order_id)
        if tax_outbox is not None and sum(p.tax_amount for p in inflow_confirmed) > 0:
            # Secondary to the cobro: a reporting bug must never break a charge,
            # so failures are logged and left for the drain to retry.
            try:
                await tax_outbox.enqueue(tenant_id, order_id)
            except Exception:  # noqa: BLE001
                logger.warning("tax report enqueue failed for order %s", order_id, exc_info=True)


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
        cash: CashSessionRepository | None = None,
        policy: CashSessionPolicy | None = None,
        fee_rates: PaymentFeeRateRepository | None = None,
        tax_outbox: TaxReportLedger | None = None,
    ) -> None:
        self._payments = payments
        self._orders = orders
        self._gateway = gateway
        self._tenant_context = tenant_context
        self._inventory = inventory
        self._sales = sales
        self._cash = cash
        self._policy = policy
        self._fee_rates = fee_rates
        self._tax_outbox = tax_outbox

    async def execute(
        self,
        *,
        tenant_id: str,
        order_id: str,
        method: str,
        amount: int,
        tip: int = 0,
        tax: int = 0,
        idempotency_key: str | None = None,
    ) -> Payment:
        self._tenant_context.set(tenant_id)
        # Idempotency (Carta QR F3): a replayed key returns the already-created
        # payment instead of charging again (a double-tapped online cobro). None →
        # no lookup (paridad: the cashier flow doesn't pass a key).
        if idempotency_key is not None:
            existing = await self._payments.get_by_idempotency_key(tenant_id, idempotency_key)
            if existing is not None:
                return existing
        # ``tax`` is the sales-tax portion INCLUDED in ``amount`` (not on top like
        # tip), so it can't be negative nor exceed the charge.
        if amount <= 0 or tip < 0 or tax < 0 or tax > amount:
            raise InvalidPaymentAmount()
        order = await self._orders.get_by_id(tenant_id, order_id)
        if order is None:
            raise OrderNotFound()
        # Caja (guarda B): estampamos la caja abierta si la hay (fase 1). Enforcement
        # (fase B3): si el tenant lo exige (flag OFF por default) y NO hay caja
        # abierta, rechazamos el cobro. Flag OFF → path idéntico a hoy (paridad).
        open_session = await self._cash.get_open(tenant_id) if self._cash else None
        if open_session is None and self._policy is not None:
            if await self._policy.requires_open_cash_session(tenant_id):
                raise NoOpenCashSession()
        # Comisiones (cimiento): estampamos lo que retiene la pasarela y el neto que
        # queda. Sin tasas cargadas → fee 0 → net == amount (paridad). Se congela por
        # cobro (estable ante cambios de tasa posteriores).
        fee_bps = 0
        if self._fee_rates is not None:
            fee_bps = (await self._fee_rates.rates_for(tenant_id)).get(method, 0)
        fee = fee_of(amount, fee_bps)
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
            cash_session_id=open_session.id if open_session else None,
            tip_amount=tip,
            tax_amount=tax,
            fee_amount=fee,
            net_amount=amount - fee,
            idempotency_key=idempotency_key,
        )
        payment = await self._gateway.charge(payment=payment)
        await self._payments.add(payment)
        await _settle_order(
            self._payments,
            self._orders,
            tenant_id,
            order.id,
            self._inventory,
            self._sales,
            self._tax_outbox,
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
        tax_outbox: TaxReportLedger | None = None,
    ) -> None:
        self._payments = payments
        self._orders = orders
        self._notifications = notifications
        self._resolver = resolver
        self._tenant_context = tenant_context
        self._inventory = inventory
        self._sales = sales
        self._tax_outbox = tax_outbox

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
            # Comisiones slice C: si la pasarela reporta la comisión REAL, pisa la
            # estimada (tasa configurada); el neto se recomputa. Sin fee → se conserva.
            if status.fee_amount is not None:
                payment.fee_amount = status.fee_amount
                payment.net_amount = payment.amount.amount - status.fee_amount
            await self._payments.save(payment)
            if payment.order_id is not None:
                await _settle_order(
                    self._payments,
                    self._orders,
                    tenant_id,
                    payment.order_id,
                    self._inventory,
                    self._sales,
                    self._tax_outbox,
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
