from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from app.application.payment.use_cases import RegisterPayment
from app.domain.identity.ports import TenantContext
from app.domain.order.entities import Order
from app.domain.order.repository import OrderRepository
from app.domain.order.value_objects import ItemStatus, SelectedOption
from app.domain.payment.entities import Payment
from app.domain.payment.exceptions import (
    InvalidPaymentAmount,
    NothingToPay,
    PaymentNotFound,
    SelfPayDisabled,
)
from app.domain.payment.repository import PaymentRepository
from app.domain.payment.self_pay_settings import SelfPaySettingsRepository
from app.domain.payment.value_objects import (
    PaymentDirection,
    PaymentMethod,
    PaymentStatus,
)
from app.domain.public_menu.exceptions import InvalidTableQrToken
from app.domain.public_menu.ports import TableQrToken
from app.domain.shared.rate_limiter import RateLimiter
from app.domain.table_session.repository import TableSessionRepository
from app.domain.tenant.repository import TenantRepository

# Rate limit (por mesa) del pago desde la mesa — mueve plata: baranda ajustada. La
# idempotency key ya dedupe el mismo intento; esto acota intentos con claves nuevas.
_PAY_LIMIT = 6
_PAY_WINDOW_S = 60


@dataclass(frozen=True)
class PublicPaymentResult:
    """What the diner's client needs after starting a cobro: where the money is
    (``status``), where to send them to pay online (``checkout_url``; None when the
    charge already confirmed — manual gateway or cash), how much was charged and
    which order it settles."""

    payment_id: str
    order_id: str
    status: str
    amount: int
    tip: int
    checkout_url: str | None


class PayTableBill:
    """Public (Carta QR F3): the diner pays their table's bill from the QR token —
    no auth, no cashier. Verifies the token, enforces the self-pay gate, resolves
    the table's oldest open order with an outstanding balance and charges exactly
    that balance (**server-computed** — a tampered client can't change it) through
    the real cobro engine with the cash policy relaxed (``RegisterPayment`` wired
    with ``cash=None``). The online gateway returns PENDING + ``checkout_url``; the
    webhook confirms and settles the order (reused as-is). One order = one charge:
    a multi-round table is paid oldest-first, one tap at a time (the front sums)."""

    def __init__(
        self,
        token: TableQrToken,
        settings: SelfPaySettingsRepository,
        sessions: TableSessionRepository,
        orders: OrderRepository,
        payments: PaymentRepository,
        register_payment: RegisterPayment,
        tenant_context: TenantContext,
        app_base_url: str,
        rate_limiter: RateLimiter,
    ) -> None:
        self._token = token
        self._settings = settings
        self._sessions = sessions
        self._orders = orders
        self._payments = payments
        self._register_payment = register_payment
        self._tenant_context = tenant_context
        self._app_base_url = app_base_url
        self._rate_limiter = rate_limiter

    async def execute(
        self,
        *,
        token: str,
        tip: int = 0,
        amount: int | None = None,
        idempotency_key: str | None = None,
    ) -> PublicPaymentResult:
        """``amount`` None → pay the order's whole remaining balance. A positive
        ``amount`` pays only that much (split the bill / pay my part); partial
        payments accumulate until the order is covered (the engine settles it).
        The amount is still bounded server-side (0 < amount ≤ balance) so a tampered
        client can neither overpay nor change what's owed."""
        claims = self._token.verify(token)  # raises InvalidTableQrToken
        tenant_id = claims.tenant_id
        await self._rate_limiter.check(
            f"pay:{tenant_id}:{claims.table_id}",
            limit=_PAY_LIMIT,
            window_seconds=_PAY_WINDOW_S,
        )
        self._tenant_context.set(tenant_id)

        cfg = await self._settings.get(tenant_id)
        if not cfg.enabled:
            raise SelfPayDisabled()
        if tip < 0:
            raise InvalidPaymentAmount()
        if not cfg.tips_enabled:
            tip = 0  # the owner turned tips off → never charge one

        session = await self._sessions.get_open_by_table(tenant_id, claims.table_id)
        if session is None:
            raise NothingToPay()

        orders = await self._orders.list_open_by_session(tenant_id, session.id)
        target = await self._first_unpaid(tenant_id, orders)
        if target is None:
            raise NothingToPay()
        order, balance = target

        charge_amount = balance
        if amount is not None:
            if amount <= 0 or amount > balance:
                raise InvalidPaymentAmount()
            charge_amount = amount

        # Where MercadoPago returns the diner after paying: back to THEIR table's
        # QR menu, so the page resumes and shows "paid" (the online flow otherwise
        # strands them on MP's success page).
        return_url = f"{self._app_base_url.rstrip('/')}/carta/{token}"

        payment = await self._register_payment.execute(
            tenant_id=tenant_id,
            order_id=order.id,
            method=PaymentMethod.MERCADOPAGO.value,
            amount=charge_amount,
            tip=tip,
            idempotency_key=idempotency_key,
            return_url=return_url,
        )
        return PublicPaymentResult(
            payment_id=payment.id,
            order_id=order.id,
            status=payment.status.value,
            amount=payment.amount.amount,
            tip=payment.tip_amount,
            checkout_url=payment.checkout_url,
        )

    async def _first_unpaid(
        self, tenant_id: str, orders: list[Order]
    ) -> tuple[Order, int] | None:
        """The oldest open order that still owes money, with its remaining balance
        (order total − confirmed inflows). ``orders`` come created-at ascending."""
        for order in orders:
            paid = 0
            for payment in await self._payments.list_by_order(tenant_id, order.id):
                if (
                    payment.direction is PaymentDirection.INFLOW
                    and payment.status is PaymentStatus.CONFIRMED
                ):
                    paid += payment.amount.amount
            balance = order.total().amount - paid
            if balance > 0:
                return order, balance
        return None


class GetPublicPaymentStatus:
    """Public (Carta QR F3): the diner's client polls the status of a charge it
    started, scoped by the table token (the payment is the token's tenant). Returns
    PENDING until the webhook confirms — the authoritative state is the gateway's,
    never the ``charge`` response."""

    def __init__(
        self,
        token: TableQrToken,
        payments: PaymentRepository,
        tenant_context: TenantContext,
    ) -> None:
        self._token = token
        self._payments = payments
        self._tenant_context = tenant_context

    async def execute(self, *, token: str, payment_id: str) -> Payment:
        claims = self._token.verify(token)  # raises InvalidTableQrToken
        self._tenant_context.set(claims.tenant_id)
        payment = await self._payments.get_by_id(claims.tenant_id, payment_id)
        if payment is None:
            raise PaymentNotFound()
        return payment


@dataclass(frozen=True)
class PublicReceiptItem:
    name: str
    quantity: int
    unit_price: int
    selected_options: list[SelectedOption] = field(default_factory=list)


@dataclass(frozen=True)
class PublicPaymentReceipt:
    """The diner's non-fiscal receipt after paying (Carta QR F3): where, what the
    table ordered, how much THIS payment covered (+tip), how and when. Not an AFIP
    invoice — that's a separate, deferred flow that needs the diner's doc."""

    venue_name: str
    currency: str
    items: list[PublicReceiptItem]
    amount: int
    tip: int
    method: str
    paid_at: datetime | None


class GetPublicPaymentReceipt:
    """Public (Carta QR F3): once a charge is confirmed, the diner can see a receipt
    of what they paid — token-scoped. The paid order has left the running bill, so
    this reads it straight from the payment's order (not from ``list_open_by_session``)."""

    def __init__(
        self,
        token: TableQrToken,
        payments: PaymentRepository,
        orders: OrderRepository,
        tenants: TenantRepository,
        tenant_context: TenantContext,
    ) -> None:
        self._token = token
        self._payments = payments
        self._orders = orders
        self._tenants = tenants
        self._tenant_context = tenant_context

    async def execute(self, *, token: str, payment_id: str) -> PublicPaymentReceipt:
        claims = self._token.verify(token)  # raises InvalidTableQrToken
        tenant_id = claims.tenant_id
        self._tenant_context.set(tenant_id)

        payment = await self._payments.get_by_id(tenant_id, payment_id)
        # Only a confirmed payment has a receipt (a pending/failed one has nothing to
        # show yet) — treat anything else as "not found" to avoid leaking state.
        if payment is None or payment.status is not PaymentStatus.CONFIRMED:
            raise PaymentNotFound()

        tenant = await self._tenants.get_by_id(tenant_id)
        if tenant is None:
            raise InvalidTableQrToken()

        items: list[PublicReceiptItem] = []
        if payment.order_id is not None:
            order = await self._orders.get_by_id(tenant_id, payment.order_id)
            if order is not None:
                items = [
                    PublicReceiptItem(
                        name=item.name,
                        quantity=item.quantity,
                        unit_price=item.unit_price.amount,
                        selected_options=list(item.selected_options),
                    )
                    for item in order.items
                    if item.status is not ItemStatus.CANCELLED
                ]

        return PublicPaymentReceipt(
            venue_name=tenant.name,
            currency=tenant.currency,
            items=items,
            amount=payment.amount.amount,
            tip=payment.tip_amount,
            method=payment.method.value,
            paid_at=payment.created_at,
        )
