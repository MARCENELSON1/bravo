from __future__ import annotations

from dataclasses import dataclass, field

from app.domain.identity.ports import TenantContext
from app.domain.order.repository import OrderRepository
from app.domain.order.value_objects import ItemStatus, SelectedOption
from app.domain.payment.credentials import ConnectionStatus, PaymentProvider
from app.domain.payment.credentials_repository import PaymentCredentialRepository
from app.domain.payment.repository import PaymentRepository
from app.domain.payment.self_pay_settings import SelfPaySettingsRepository
from app.domain.payment.value_objects import PaymentDirection, PaymentStatus
from app.domain.public_menu.exceptions import InvalidTableQrToken
from app.domain.public_menu.ports import TableQrToken
from app.domain.table_session.repository import TableSessionRepository
from app.domain.tenant.repository import TenantRepository

_PROVIDER = PaymentProvider.MERCADOPAGO.value


@dataclass(frozen=True)
class TableBillItem:
    """One line of the running table bill (display-only). ``unit_price`` already
    folds any modifier deltas (F2), and ``selected_options`` is the kitchen-ticket
    snapshot the diner sees echoed back."""

    name: str
    quantity: int
    unit_price: int
    selected_options: list[SelectedOption] = field(default_factory=list)


@dataclass(frozen=True)
class TableBill:
    """The diner-facing bill for a table: what was ordered, the total, how much is
    already settled and what's left. Money is server-computed (never trusted from
    the client). ``online_pay_available`` tells the front whether to offer online
    pay (self-pay enabled + MercadoPago connected) or fall back to "pay with the
    waiter". ``tips_enabled`` gates the tip selector."""

    currency: str
    items: list[TableBillItem]
    total: int
    paid: int
    balance: int
    online_pay_available: bool
    tips_enabled: bool


class GetTableBill:
    """Public (Carta QR F3): the diner reads the running bill of their table from
    the QR token — no auth. Verifies the token, resolves the table's open floor
    session, sums its open orders (total), subtracts the confirmed inflows (paid)
    and returns the balance. Read-only, no money moves here."""

    def __init__(
        self,
        token: TableQrToken,
        tenants: TenantRepository,
        sessions: TableSessionRepository,
        orders: OrderRepository,
        payments: PaymentRepository,
        settings: SelfPaySettingsRepository,
        credentials: PaymentCredentialRepository,
        tenant_context: TenantContext,
        assume_connected: bool = False,
    ) -> None:
        self._token = token
        self._tenants = tenants
        self._sessions = sessions
        self._orders = orders
        self._payments = payments
        self._settings = settings
        self._credentials = credentials
        self._tenant_context = tenant_context
        self._assume_connected = assume_connected

    async def execute(self, *, token: str) -> TableBill:
        claims = self._token.verify(token)  # raises InvalidTableQrToken
        tenant_id = claims.tenant_id
        self._tenant_context.set(tenant_id)

        tenant = await self._tenants.get_by_id(tenant_id)
        if tenant is None:
            # Signed token for a tenant that no longer exists → treat as invalid
            # rather than leaking that distinction (mirrors GetPublicMenu).
            raise InvalidTableQrToken()

        cfg = await self._settings.get(tenant_id)
        online_pay_available = cfg.enabled and await self._mp_connected(tenant_id)

        session = await self._sessions.get_open_by_table(tenant_id, claims.table_id)
        if session is None:
            return TableBill(
                currency=tenant.currency,
                items=[],
                total=0,
                paid=0,
                balance=0,
                online_pay_available=online_pay_available,
                tips_enabled=cfg.tips_enabled,
            )

        orders = await self._orders.list_open_by_session(tenant_id, session.id)
        items: list[TableBillItem] = []
        total = 0
        paid = 0
        for order in orders:
            total += order.total().amount
            for item in order.items:
                if item.status is ItemStatus.CANCELLED:
                    continue
                items.append(
                    TableBillItem(
                        name=item.name,
                        quantity=item.quantity,
                        unit_price=item.unit_price.amount,
                        selected_options=list(item.selected_options),
                    )
                )
            for payment in await self._payments.list_by_order(tenant_id, order.id):
                if (
                    payment.direction is PaymentDirection.INFLOW
                    and payment.status is PaymentStatus.CONFIRMED
                ):
                    paid += payment.amount.amount

        return TableBill(
            currency=tenant.currency,
            items=items,
            total=total,
            paid=paid,
            balance=max(total - paid, 0),  # never show a negative saldo
            online_pay_available=online_pay_available,
            tips_enabled=cfg.tips_enabled,
        )

    async def _mp_connected(self, tenant_id: str) -> bool:
        # Single-account/demo: la plataforma cobra con su propio token → se ofrece
        # pago online sin OAuth por tenant.
        if self._assume_connected:
            return True
        credential = await self._credentials.get_by_tenant(tenant_id, _PROVIDER)
        return credential is not None and credential.status is ConnectionStatus.CONNECTED
