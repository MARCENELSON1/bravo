"""Unit tests for GetTableBill (Carta QR F3 Tanda A): the diner's read-only bill.

Aggregates the open orders of a table's floor session, subtracts confirmed inflows
and never trusts the client. Fakes stand in for every port; the token is the real
HMAC one (the scope)."""

from __future__ import annotations

import pytest

from app.application.order.table_bill import GetTableBill
from app.domain.order.entities import Order, OrderItem
from app.domain.order.value_objects import ItemStatus, OrderStatus, SelectedOption
from app.domain.payment.credentials import (
    ConnectionStatus,
    PaymentCredential,
    PaymentProvider,
)
from app.domain.payment.entities import Payment
from app.domain.payment.self_pay_settings import SelfPaySettings
from app.domain.payment.value_objects import (
    PaymentDirection,
    PaymentMethod,
    PaymentStatus,
)
from app.domain.public_menu.exceptions import InvalidTableQrToken
from app.domain.shared.money import Money
from app.domain.table_session.entities import TableSession
from app.domain.tenant.entities import Tenant
from app.infrastructure.public_menu.signed_table_qr import HmacTableQrToken
from tests.fakes import FakeTenantContext

_SECRET = "s3cr3t"


class _FakeTenants:
    def __init__(self, tenant: Tenant | None) -> None:
        self._tenant = tenant

    async def get_by_id(self, tenant_id: str) -> Tenant | None:
        return self._tenant


class _FakeSessions:
    def __init__(self, session: TableSession | None) -> None:
        self._session = session

    async def get_open_by_table(self, tenant_id: str, table_id: str) -> TableSession | None:
        return self._session


class _FakeOrders:
    def __init__(self, orders: list[Order]) -> None:
        self._orders = orders

    async def list_open_by_session(self, tenant_id: str, session_id: str) -> list[Order]:
        return [o for o in self._orders if o.session_id == session_id]


class _FakePayments:
    def __init__(self, by_order: dict[str, list[Payment]]) -> None:
        self._by_order = by_order

    async def list_by_order(self, tenant_id: str, order_id: str) -> list[Payment]:
        return self._by_order.get(order_id, [])


class _FakeSettings:
    def __init__(self, settings: SelfPaySettings) -> None:
        self._settings = settings

    async def get(self, tenant_id: str) -> SelfPaySettings:
        return self._settings


class _FakeCredentials:
    def __init__(self, credential: PaymentCredential | None) -> None:
        self._credential = credential

    async def get_by_tenant(self, tenant_id: str, provider: str) -> PaymentCredential | None:
        return self._credential


def _tenant() -> Tenant:
    return Tenant(id="t1", slug="resto", name="Resto", currency="ARS")


def _item(
    name: str, price: int, qty: int, options: list[SelectedOption] | None = None
) -> OrderItem:
    return OrderItem(
        id=f"i-{name}",
        product_id="p",
        name=name,
        unit_price=Money(price, "ARS"),
        quantity=qty,
        status=ItemStatus.SENT,
        selected_options=options or [],
    )


def _order(order_id: str, items: list[OrderItem], session_id: str = "sess-1") -> Order:
    return Order(
        id=order_id,
        tenant_id="t1",
        table_id="tbl-1",
        waiter_id="w",
        currency="ARS",
        status=OrderStatus.SENT,
        items=items,
        session_id=session_id,
    )


def _inflow(amount: int, status: PaymentStatus, order_id: str) -> Payment:
    return Payment(
        id=f"pay-{order_id}-{amount}-{status}",
        tenant_id="t1",
        direction=PaymentDirection.INFLOW,
        amount=Money(amount, "ARS"),
        method=PaymentMethod.MERCADOPAGO,
        status=status,
        order_id=order_id,
    )


def _credential() -> PaymentCredential:
    return PaymentCredential(
        id="c1",
        tenant_id="t1",
        provider=PaymentProvider.MERCADOPAGO,
        external_account_id="seller-1",
        access_token="tok",
        status=ConnectionStatus.CONNECTED,
    )


def _use_case(
    *,
    tenant: Tenant | None,
    session: TableSession | None,
    orders: list[Order],
    payments: dict[str, list[Payment]],
    settings: SelfPaySettings,
    credential: PaymentCredential | None,
    assume_connected: bool = False,
) -> tuple[GetTableBill, HmacTableQrToken]:
    token = HmacTableQrToken(secret=_SECRET)
    uc = GetTableBill(
        token=token,
        tenants=_FakeTenants(tenant),  # type: ignore[arg-type]
        sessions=_FakeSessions(session),  # type: ignore[arg-type]
        orders=_FakeOrders(orders),  # type: ignore[arg-type]
        payments=_FakePayments(payments),  # type: ignore[arg-type]
        settings=_FakeSettings(settings),  # type: ignore[arg-type]
        credentials=_FakeCredentials(credential),  # type: ignore[arg-type]
        tenant_context=FakeTenantContext(),
        assume_connected=assume_connected,
    )
    return uc, token


async def test_aggregates_orders_and_subtracts_confirmed_inflows() -> None:
    session = TableSession(id="sess-1", tenant_id="t1", table_id="tbl-1")
    orders = [
        _order("o1", [_item("Pizza", 1200000, 2)]),  # 2_400_000
        _order("o2", [_item("Agua", 300000, 1)]),  # 300_000
    ]
    payments = {"o1": [_inflow(1000000, PaymentStatus.CONFIRMED, "o1")]}
    uc, token = _use_case(
        tenant=_tenant(),
        session=session,
        orders=orders,
        payments=payments,
        settings=SelfPaySettings(enabled=True),
        credential=_credential(),
    )

    bill = await uc.execute(token=token.issue("t1", "tbl-1"))

    assert bill.currency == "ARS"
    assert bill.total == 2_700_000
    assert bill.paid == 1_000_000
    assert bill.balance == 1_700_000
    assert [(i.name, i.quantity, i.unit_price) for i in bill.items] == [
        ("Pizza", 2, 1200000),
        ("Agua", 1, 300000),
    ]
    assert bill.online_pay_available is True
    assert bill.tips_enabled is True


async def test_only_confirmed_inflows_count_towards_paid() -> None:
    session = TableSession(id="sess-1", tenant_id="t1", table_id="tbl-1")
    orders = [_order("o1", [_item("Pizza", 1000000, 1)])]
    # A pending charge and a refunded one must NOT reduce the balance; only CONFIRMED.
    payments = {
        "o1": [
            _inflow(400000, PaymentStatus.CONFIRMED, "o1"),
            _inflow(500000, PaymentStatus.PENDING, "o1"),
            _inflow(300000, PaymentStatus.REFUNDED, "o1"),
        ]
    }
    uc, token = _use_case(
        tenant=_tenant(),
        session=session,
        orders=orders,
        payments=payments,
        settings=SelfPaySettings(),
        credential=None,
    )

    bill = await uc.execute(token=token.issue("t1", "tbl-1"))

    assert bill.paid == 400000
    assert bill.balance == 600000


async def test_balance_never_negative_when_overpaid() -> None:
    session = TableSession(id="sess-1", tenant_id="t1", table_id="tbl-1")
    orders = [_order("o1", [_item("Pizza", 1000000, 1)])]
    payments = {"o1": [_inflow(1200000, PaymentStatus.CONFIRMED, "o1")]}
    uc, token = _use_case(
        tenant=_tenant(),
        session=session,
        orders=orders,
        payments=payments,
        settings=SelfPaySettings(),
        credential=None,
    )

    bill = await uc.execute(token=token.issue("t1", "tbl-1"))

    assert bill.balance == 0


async def test_cancelled_items_are_excluded_from_the_bill() -> None:
    session = TableSession(id="sess-1", tenant_id="t1", table_id="tbl-1")
    cancelled = _item("Anulado", 900000, 1)
    cancelled.status = ItemStatus.CANCELLED
    orders = [_order("o1", [_item("Pizza", 1000000, 1), cancelled])]
    uc, token = _use_case(
        tenant=_tenant(),
        session=session,
        orders=orders,
        payments={},
        settings=SelfPaySettings(),
        credential=None,
    )

    bill = await uc.execute(token=token.issue("t1", "tbl-1"))

    assert bill.total == 1_000_000
    assert [i.name for i in bill.items] == ["Pizza"]


async def test_modifier_snapshot_travels_to_the_bill_item() -> None:
    session = TableSession(id="sess-1", tenant_id="t1", table_id="tbl-1")
    options = [SelectedOption("opt-1", "Con panceta", 300000)]
    orders = [_order("o1", [_item("Burger", 1500000, 1, options)])]
    uc, token = _use_case(
        tenant=_tenant(),
        session=session,
        orders=orders,
        payments={},
        settings=SelfPaySettings(),
        credential=None,
    )

    bill = await uc.execute(token=token.issue("t1", "tbl-1"))

    assert bill.items[0].selected_options == options


async def test_empty_bill_when_no_open_session() -> None:
    uc, token = _use_case(
        tenant=_tenant(),
        session=None,
        orders=[],
        payments={},
        settings=SelfPaySettings(enabled=True, tips_enabled=False),
        credential=_credential(),
    )

    bill = await uc.execute(token=token.issue("t1", "tbl-1"))

    assert bill.items == []
    assert bill.total == 0
    assert bill.balance == 0
    # Config still surfaces, so the diner sees online pay / tip state on an empty tab.
    assert bill.online_pay_available is True
    assert bill.tips_enabled is False


@pytest.mark.parametrize(
    ("enabled", "connected", "expected"),
    [
        (True, True, True),
        (True, False, False),  # enabled but MP not connected → no online pay
        (False, True, False),  # MP connected but owner didn't enable self-pay
        (False, False, False),
    ],
)
async def test_online_pay_available_requires_enabled_and_connected(
    enabled: bool, connected: bool, expected: bool
) -> None:
    uc, token = _use_case(
        tenant=_tenant(),
        session=None,
        orders=[],
        payments={},
        settings=SelfPaySettings(enabled=enabled),
        credential=_credential() if connected else None,
    )

    bill = await uc.execute(token=token.issue("t1", "tbl-1"))

    assert bill.online_pay_available is expected


async def test_assume_connected_makes_online_pay_available_without_a_credential() -> None:
    # Single-account/demo: sin credencial OAuth por tenant, pero con el flag → online.
    uc, token = _use_case(
        tenant=_tenant(),
        session=None,
        orders=[],
        payments={},
        settings=SelfPaySettings(enabled=True),
        credential=None,
        assume_connected=True,
    )

    bill = await uc.execute(token=token.issue("t1", "tbl-1"))

    assert bill.online_pay_available is True


async def test_bad_token_rejected() -> None:
    uc, _token = _use_case(
        tenant=_tenant(),
        session=None,
        orders=[],
        payments={},
        settings=SelfPaySettings(),
        credential=None,
    )
    with pytest.raises(InvalidTableQrToken):
        await uc.execute(token="garbage.deadbeef")


async def test_unknown_tenant_is_treated_as_invalid_token() -> None:
    uc, token = _use_case(
        tenant=None,  # signed token for a tenant that no longer exists
        session=None,
        orders=[],
        payments={},
        settings=SelfPaySettings(),
        credential=None,
    )
    with pytest.raises(InvalidTableQrToken):
        await uc.execute(token=token.issue("t1", "tbl-1"))
