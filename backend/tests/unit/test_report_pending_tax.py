from __future__ import annotations

from app.application.tax.reporting import (
    PendingTaxReport,
    ReportPendingTaxSales,
    TaxReportLedger,
)
from app.domain.payment.value_objects import PaymentDirection, PaymentStatus
from app.domain.shared.money import Money
from app.domain.tax.ports import TaxReporter, TaxReporterResolver
from app.domain.tax.value_objects import TaxSale
from app.domain.tenant.entities import Tenant
from app.domain.tenant.regional import TaxEngine, TaxRegime


class _StubOrder:
    def __init__(self, order_id: str, total: Money) -> None:
        self.id = order_id
        self._total = total

    def total(self) -> Money:
        return self._total


class _StubPayment:
    def __init__(self, tax_amount: int) -> None:
        self.tax_amount = tax_amount
        self.direction = PaymentDirection.INFLOW
        self.status = PaymentStatus.CONFIRMED


class _FakeOrders:
    def __init__(self, orders: dict[str, _StubOrder]) -> None:
        self._orders = orders

    async def get_by_id(self, tenant_id: str, order_id: str) -> _StubOrder | None:
        return self._orders.get(order_id)


class _FakePayments:
    def __init__(self, by_order: dict[str, list[_StubPayment]]) -> None:
        self._by_order = by_order

    async def list_by_order(self, tenant_id: str, order_id: str) -> list[_StubPayment]:
        return self._by_order.get(order_id, [])


class _FakeTenants:
    def __init__(self, tenant: Tenant) -> None:
        self._tenant = tenant

    async def get_by_id(self, tenant_id: str) -> Tenant:
        return self._tenant


class _NoopCtx:
    def set(self, tenant_id: str) -> None:
        pass


class _FakeLedger(TaxReportLedger):
    def __init__(self, pending: list[PendingTaxReport]) -> None:
        self._pending = pending
        self.sent: dict[str, str] = {}
        self.failed: dict[str, str] = {}

    async def enqueue(self, tenant_id: str, order_id: str) -> None:  # pragma: no cover
        pass

    async def list_pending(self, tenant_id: str, *, limit: int = 100) -> list[PendingTaxReport]:
        return self._pending

    async def mark_sent(self, report_id: str, external_id: str) -> None:
        self.sent[report_id] = external_id

    async def mark_failed(self, report_id: str, error: str) -> None:
        self.failed[report_id] = error


class _FakeReporter(TaxReporter):
    def __init__(self, fail_on: set[str] | None = None) -> None:
        self.fail_on = fail_on or set()
        self.reported: list[TaxSale] = []

    async def report_sale(self, sale: TaxSale) -> str:
        if sale.transaction_id in self.fail_on:
            raise RuntimeError("provider down")
        self.reported.append(sale)
        return f"ext-{sale.transaction_id}"


class _FakeResolver(TaxReporterResolver):
    """Returns the tenant's reporter, or None when TaxJar isn't connected."""

    def __init__(self, reporter: TaxReporter | None) -> None:
        self._reporter = reporter

    async def reporter_for(self, tenant_id: str) -> TaxReporter | None:
        return self._reporter


def _tenant() -> Tenant:
    return Tenant(
        id="t1",
        slug="s",
        name="n",
        country="US",
        currency="USD",
        tax_engine=TaxEngine.TAXJAR,
        tax_regime=TaxRegime.US_SALES_TAX,
        fiscal_state="CA",
        fiscal_zip="90404",
    )


def _use_case(ledger, reporter, orders, payments):
    return ReportPendingTaxSales(
        ledger=ledger,
        resolver=_FakeResolver(reporter),
        orders=orders,
        payments=payments,
        tenants=_FakeTenants(_tenant()),
        tenant_context=_NoopCtx(),
    )


async def test_drains_pending_and_marks_sent():
    ledger = _FakeLedger(
        [PendingTaxReport(id="r1", order_id="o1", occurred_at="2026-08-25T00:00:00")]
    )
    reporter = _FakeReporter()
    orders = _FakeOrders({"o1": _StubOrder("o1", Money(10000, "USD"))})
    payments = _FakePayments({"o1": [_StubPayment(1075)]})

    run = await _use_case(ledger, reporter, orders, payments).execute(tenant_id="t1")

    assert (run.pending, run.sent, run.failed) == (1, 1, 0)
    assert ledger.sent == {"r1": "ext-o1"}
    # The reported sale carries the pre-tax subtotal + the collected tax separately.
    sale = reporter.reported[0]
    assert sale.amount == Money(10000, "USD")
    assert sale.sales_tax == Money(1075, "USD")
    assert sale.transaction_id == "o1"


async def test_one_failure_is_isolated_others_still_sent():
    ledger = _FakeLedger(
        [
            PendingTaxReport(id="r1", order_id="o1", occurred_at="2026-08-25T00:00:00"),
            PendingTaxReport(id="r2", order_id="o2", occurred_at="2026-08-25T00:00:00"),
        ]
    )
    reporter = _FakeReporter(fail_on={"o1"})
    orders = _FakeOrders(
        {"o1": _StubOrder("o1", Money(10000, "USD")), "o2": _StubOrder("o2", Money(5000, "USD"))}
    )
    payments = _FakePayments({"o1": [_StubPayment(1075)], "o2": [_StubPayment(500)]})

    run = await _use_case(ledger, reporter, orders, payments).execute(tenant_id="t1")

    # o1 fails (stays retryable via FAILED), o2 succeeds — the run doesn't abort.
    assert (run.pending, run.sent, run.failed) == (2, 1, 1)
    assert ledger.sent == {"r2": "ext-o2"}
    assert "r1" in ledger.failed


async def test_empty_outbox_is_noop():
    # AR shape: nothing enqueued → all-zeros, no provider calls (parity).
    reporter = _FakeReporter()
    run = await _use_case(
        _FakeLedger([]), reporter, _FakeOrders({}), _FakePayments({})
    ).execute(tenant_id="t1")
    assert (run.pending, run.sent, run.failed) == (0, 0, 0)
    assert reporter.reported == []


async def test_not_connected_marks_rows_failed_without_filing():
    # Tenant hasn't connected TaxJar → resolver returns None → every pending row
    # fails (visible, retryable), never filed under a shared platform account.
    ledger = _FakeLedger(
        [PendingTaxReport(id="r1", order_id="o1", occurred_at="2026-08-25T00:00:00")]
    )
    orders = _FakeOrders({"o1": _StubOrder("o1", Money(10000, "USD"))})
    payments = _FakePayments({"o1": [_StubPayment(1075)]})

    run = await _use_case(ledger, None, orders, payments).execute(tenant_id="t1")

    assert (run.pending, run.sent, run.failed) == (1, 0, 1)
    assert ledger.sent == {}
    assert "taxjar_not_connected" in ledger.failed["r1"]
