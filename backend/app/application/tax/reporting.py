"""Reporting collected sales tax to the provider (TaxJar AutoFile).

Two moving parts, kept apart on purpose:

* the **outbox** (``TaxReportLedger``): on the PAID transition, an order that
  collected sales tax is enqueued with a local, reliable insert (idempotent on
  ``order_id``). No network call touches the cobro — if the provider is down the
  charge still succeeds and the sale waits in the ledger.
* the **drain** (``ReportPendingTaxSales``): pushes pending sales to the provider
  out of band, isolating failures per row so one bad sale (or a provider outage)
  never aborts the run; failed rows stay pending and are retried next drain.

AR never reaches any of this: it collects no sales tax, so nothing is enqueued.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.domain.identity.ports import TenantContext
from app.domain.order.repository import OrderRepository
from app.domain.payment.repository import PaymentRepository
from app.domain.payment.value_objects import PaymentDirection, PaymentStatus
from app.domain.shared.money import Money
from app.domain.tax.ports import TaxReporter
from app.domain.tax.value_objects import FiscalAddress, TaxSale
from app.domain.tenant.repository import TenantRepository


@dataclass(frozen=True)
class PendingTaxReport:
    """A sale awaiting (or retrying) its report to the tax provider."""

    id: str
    order_id: str
    occurred_at: str  # ISO-8601; becomes the provider's transaction_date


@dataclass(frozen=True)
class TaxReportRun:
    """Outcome of a drain pass, for the caller to surface honestly."""

    pending: int
    sent: int
    failed: int


class TaxReportLedger(ABC):
    """Durable outbox of taxable sales to report. Tenant-scoped."""

    @abstractmethod
    async def enqueue(self, tenant_id: str, order_id: str) -> None:
        """Mark an order as needing a tax report. Idempotent per (tenant, order)."""

    @abstractmethod
    async def list_pending(self, tenant_id: str, *, limit: int = 100) -> list[PendingTaxReport]:
        """Rows still to send (never sent, or last attempt failed)."""

    @abstractmethod
    async def mark_sent(self, report_id: str, external_id: str) -> None: ...

    @abstractmethod
    async def mark_failed(self, report_id: str, error: str) -> None: ...


def _fiscal_address(tenant) -> FiscalAddress:  # noqa: ANN001 (domain Tenant)
    return FiscalAddress(
        street=tenant.fiscal_street or "",
        city=tenant.fiscal_city or "",
        state=tenant.fiscal_state or "",
        zip=tenant.fiscal_zip or "",
        country=tenant.country or "US",
    )


class ReportPendingTaxSales:
    """Drain the outbox: report each pending taxable sale to the provider.

    Per-row isolation is the whole point — a provider outage or one malformed
    sale marks that row failed (stays retryable) without stopping the rest. AR
    tenants have an empty outbox, so this returns all-zeros (parity)."""

    def __init__(
        self,
        ledger: TaxReportLedger,
        reporter: TaxReporter,
        orders: OrderRepository,
        payments: PaymentRepository,
        tenants: TenantRepository,
        tenant_context: TenantContext,
    ) -> None:
        self._ledger = ledger
        self._reporter = reporter
        self._orders = orders
        self._payments = payments
        self._tenants = tenants
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str, limit: int = 100) -> TaxReportRun:
        self._tenant_context.set(tenant_id)
        pending = await self._ledger.list_pending(tenant_id, limit=limit)
        sent = 0
        failed = 0
        tenant = await self._tenants.get_by_id(tenant_id)
        for row in pending:
            try:
                sale = await self._build_sale(tenant_id, tenant, row)
                external_id = await self._reporter.report_sale(sale)
                await self._ledger.mark_sent(row.id, external_id)
                sent += 1
            except Exception as exc:  # noqa: BLE001 — isolate one bad sale / outage
                await self._ledger.mark_failed(row.id, str(exc)[:500])
                failed += 1
        return TaxReportRun(pending=len(pending), sent=sent, failed=failed)

    async def _build_sale(self, tenant_id: str, tenant, row: PendingTaxReport) -> TaxSale:  # noqa: ANN001
        order = await self._orders.get_by_id(tenant_id, row.order_id)
        if order is None or tenant is None:
            raise ValueError("order_or_tenant_missing")
        payments = await self._payments.list_by_order(tenant_id, row.order_id)
        tax = sum(
            p.tax_amount
            for p in payments
            if p.direction is PaymentDirection.INFLOW and p.status is PaymentStatus.CONFIRMED
        )
        subtotal = order.total()  # pre-tax line total; provider re-adds the tax
        return TaxSale(
            transaction_id=order.id,
            amount=subtotal,
            sales_tax=Money(tax, subtotal.currency),
            address=_fiscal_address(tenant),
            occurred_at=row.occurred_at,
        )
