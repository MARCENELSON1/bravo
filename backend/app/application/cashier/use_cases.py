from __future__ import annotations

from uuid import uuid4

from app.application.cashier.dtos import CashMovementRow, CashReport, CashReportLine
from app.application.clock import utcnow
from app.domain.cashier.entities import CashCount, CashMovement, CashSession
from app.domain.cashier.exceptions import (
    CashSessionAlreadyOpen,
    CashSessionNotFound,
    NoOpenCashSession,
)
from app.domain.cashier.repository import (
    CashMovementRepository,
    CashSessionRepository,
)
from app.domain.cashier.value_objects import CashMovementKind, CashSessionStatus
from app.domain.identity.ports import TenantContext
from app.domain.payment.repository import PaymentRepository
from app.domain.payment.value_objects import PaymentMethod
from app.domain.shared.exceptions import InvalidMoneyAmount
from app.domain.shared.money import Money
from app.domain.tenant.exceptions import TenantNotFound
from app.domain.tenant.repository import TenantRepository


async def _arqueo_inputs(
    session: CashSession,
    payments: PaymentRepository,
    movements: list[CashMovement],
) -> tuple[dict[str, int], dict[str, int]]:
    """``(expected_by_method, tips_by_method)`` for the session window.

    ``expected`` is what the drawer/batch should hold per method: the confirmed
    sale inflows + the propinas (a tip is collected money too) + the opening cash
    float on CASH + the net of the manual cash-drawer movements (ingresos −
    sangrías/pagos). ``tips`` is the propina component on its own (already inside
    ``expected``) so the cashier can set it aside for the staff."""
    until = session.closed_at or utcnow()
    since = session.opened_at or until
    sales = await payments.confirmed_inflows_by_method(session.tenant_id, since, until)
    tips = await payments.confirmed_tips_by_method(session.tenant_id, since, until)
    expected = {m: sales.get(m, 0) + tips.get(m, 0) for m in set(sales) | set(tips)}
    cash = PaymentMethod.CASH.value
    movements_net = sum(mv.signed_amount for mv in movements)
    expected[cash] = expected.get(cash, 0) + session.opening_float.amount + movements_net
    return expected, dict(tips)


def _build_report(
    session: CashSession,
    expected: dict[str, int],
    tips: dict[str, int],
    movements: list[CashMovement],
) -> CashReport:
    counted = {c.method.value: c.counted.amount for c in session.counts}
    closed = session.status is CashSessionStatus.CLOSED
    methods = sorted(set(expected) | set(counted))
    lines = [
        CashReportLine(
            method=m,
            expected=expected.get(m, 0),
            tips=tips.get(m, 0),
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
    cash_in = sum(mv.amount.amount for mv in movements if mv.kind.is_inflow)
    cash_out = sum(mv.amount.amount for mv in movements if not mv.kind.is_inflow)
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
        tips_total=sum(tips.values()),
        movements=[
            CashMovementRow(
                id=mv.id,
                kind=mv.kind.value,
                amount=mv.amount.amount,
                signed_amount=mv.signed_amount,
                reason=mv.reason,
                created_at=mv.created_at,
            )
            for mv in movements
        ],
        cash_in_total=cash_in,
        cash_out_total=cash_out,
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
        movements: CashMovementRepository,
        tenant_context: TenantContext,
    ) -> None:
        self._cash = cash
        self._payments = payments
        self._movements = movements
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str) -> CashReport | None:
        self._tenant_context.set(tenant_id)
        session = await self._cash.get_open(tenant_id)
        if session is None:
            return None
        movements = await self._movements.list_for_session(tenant_id, session.id)
        expected, tips = await _arqueo_inputs(session, self._payments, movements)
        return _build_report(session, expected, tips, movements)


class RegisterCashMovement:
    """Record a manual cash-drawer movement (sangría / ingreso / pago en efectivo)
    on the currently open register. Reconciles the arqueo Z; it is NOT a sale and
    does NOT create an expense (that stays a separate call)."""

    def __init__(
        self,
        cash: CashSessionRepository,
        movements: CashMovementRepository,
        tenant_context: TenantContext,
    ) -> None:
        self._cash = cash
        self._movements = movements
        self._tenant_context = tenant_context

    async def execute(
        self,
        *,
        tenant_id: str,
        kind: str,
        amount: int,
        created_by: str,
        reason: str | None = None,
    ) -> CashMovement:
        self._tenant_context.set(tenant_id)
        if amount <= 0:
            raise InvalidMoneyAmount()
        session = await self._cash.get_open(tenant_id)
        if session is None:
            raise NoOpenCashSession()
        movement = CashMovement(
            id=str(uuid4()),
            tenant_id=tenant_id,
            cash_session_id=session.id,
            kind=CashMovementKind(kind),
            amount=Money(amount, session.currency),
            created_by=created_by,
            reason=reason,
            created_at=utcnow(),
        )
        await self._movements.add(movement)
        return movement


class CloseCashSession:
    """Close a register turn: record the counted amount per method and compute the
    arqueo Z (esperado vs contado, diferencia por medio)."""

    def __init__(
        self,
        cash: CashSessionRepository,
        payments: PaymentRepository,
        movements: CashMovementRepository,
        tenant_context: TenantContext,
    ) -> None:
        self._cash = cash
        self._payments = payments
        self._movements = movements
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
        movements = await self._movements.list_for_session(tenant_id, session.id)
        expected, tips = await _arqueo_inputs(session, self._payments, movements)
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
        return _build_report(session, expected, tips, movements)
