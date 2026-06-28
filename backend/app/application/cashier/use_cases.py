from __future__ import annotations

from uuid import uuid4

from app.application.cashier.dtos import CashReport, CashReportLine
from app.application.clock import utcnow
from app.domain.cashier.entities import CashCount, CashSession
from app.domain.cashier.exceptions import (
    CashSessionAlreadyOpen,
    CashSessionNotFound,
)
from app.domain.cashier.repository import CashSessionRepository
from app.domain.cashier.value_objects import CashSessionStatus
from app.domain.identity.ports import TenantContext
from app.domain.payment.repository import PaymentRepository
from app.domain.payment.value_objects import PaymentMethod
from app.domain.shared.money import Money
from app.domain.tenant.exceptions import TenantNotFound
from app.domain.tenant.repository import TenantRepository


async def _expected_by_method(
    session: CashSession, payments: PaymentRepository
) -> dict[str, int]:
    """Sum of confirmed inflows per method during the session, with the opening
    cash float added to CASH (it's physically in the drawer at count time)."""
    until = session.closed_at or utcnow()
    expected = dict(
        await payments.confirmed_inflows_by_method(
            session.tenant_id, session.opened_at or until, until
        )
    )
    cash = PaymentMethod.CASH.value
    expected[cash] = expected.get(cash, 0) + session.opening_float.amount
    return expected


def _build_report(session: CashSession, expected: dict[str, int]) -> CashReport:
    counted = {c.method.value: c.counted.amount for c in session.counts}
    closed = session.status is CashSessionStatus.CLOSED
    methods = sorted(set(expected) | set(counted))
    lines = [
        CashReportLine(
            method=m,
            expected=expected.get(m, 0),
            counted=counted.get(m, 0) if closed else None,
            difference=(counted.get(m, 0) - expected.get(m, 0)) if closed else None,
        )
        for m in methods
    ]
    expected_total = sum(expected.values())
    counted_total = sum(counted.values()) if closed else None
    difference_total = (
        counted_total - expected_total if counted_total is not None else None
    )
    return CashReport(
        session_id=session.id,
        status=session.status.value,
        currency=session.currency,
        opening_float=session.opening_float.amount,
        opened_at=session.opened_at,
        closed_at=session.closed_at,
        lines=lines,
        expected_total=expected_total,
        counted_total=counted_total,
        difference_total=difference_total,
    )


class OpenCashSession:
    """Open a register turn with a starting cash float (one open caja at a time)."""

    def __init__(
        self,
        cash: CashSessionRepository,
        tenants: TenantRepository,
        tenant_context: TenantContext,
    ) -> None:
        self._cash = cash
        self._tenants = tenants
        self._tenant_context = tenant_context

    async def execute(
        self,
        *,
        tenant_id: str,
        opened_by: str,
        opening_float_amount: int,
        note: str | None = None,
    ) -> CashSession:
        self._tenant_context.set(tenant_id)
        if await self._cash.get_open(tenant_id) is not None:
            raise CashSessionAlreadyOpen()
        tenant = await self._tenants.get_by_id(tenant_id)
        if tenant is None:
            raise TenantNotFound()
        session = CashSession(
            id=str(uuid4()),
            tenant_id=tenant_id,
            opened_by=opened_by,
            opening_float=Money(opening_float_amount, tenant.currency),
            currency=tenant.currency,
            opened_at=utcnow(),
            note=note,
        )
        await self._cash.add(session)
        return session


class GetCurrentCashReport:
    """The live arqueo Z of the currently open register (None if none is open)."""

    def __init__(
        self,
        cash: CashSessionRepository,
        payments: PaymentRepository,
        tenant_context: TenantContext,
    ) -> None:
        self._cash = cash
        self._payments = payments
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str) -> CashReport | None:
        self._tenant_context.set(tenant_id)
        session = await self._cash.get_open(tenant_id)
        if session is None:
            return None
        expected = await _expected_by_method(session, self._payments)
        return _build_report(session, expected)


class CloseCashSession:
    """Close a register turn: record the counted amount per method and compute the
    arqueo Z (esperado vs contado, diferencia por medio)."""

    def __init__(
        self,
        cash: CashSessionRepository,
        payments: PaymentRepository,
        tenant_context: TenantContext,
    ) -> None:
        self._cash = cash
        self._payments = payments
        self._tenant_context = tenant_context

    async def execute(
        self,
        *,
        tenant_id: str,
        session_id: str,
        counted: dict[str, int],
        closed_by: str,
        note: str | None = None,
    ) -> CashReport:
        self._tenant_context.set(tenant_id)
        session = await self._cash.get_by_id(tenant_id, session_id)
        if session is None:
            raise CashSessionNotFound()
        expected = await _expected_by_method(session, self._payments)
        counts = [
            CashCount(
                method=PaymentMethod(m),
                expected=Money(expected.get(m, 0), session.currency),
                counted=Money(counted.get(m, 0), session.currency),
            )
            for m in sorted(set(expected) | set(counted))
        ]
        session.close(counts, utcnow(), closed_by, note)
        await self._cash.save(session)
        return _build_report(session, expected)
