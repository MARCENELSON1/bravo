from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from app.domain.cashier.exceptions import CashSessionAlreadyClosed
from app.domain.cashier.value_objects import CashSessionStatus
from app.domain.payment.value_objects import PaymentMethod
from app.domain.shared.money import Money


@dataclass
class CashCount:
    """One line of the arqueo Z: what the system expected for a payment method
    vs what the cashier actually counted. The difference is a signed integer in
    minor units (negative = faltante), so it lives outside ``Money`` (which is
    non-negative)."""

    method: PaymentMethod
    expected: Money
    counted: Money

    @property
    def difference_amount(self) -> int:
        return self.counted.amount - self.expected.amount


@dataclass
class CashSession:
    """A register turn (caja), scoped to a tenant. Opens with a cash float and
    closes with a per-method count → the arqueo Z (esperado vs contado)."""

    id: str
    tenant_id: str
    opened_by: str
    opening_float: Money
    currency: str
    status: CashSessionStatus = CashSessionStatus.OPEN
    opened_at: datetime | None = None
    closed_at: datetime | None = None
    closed_by: str | None = None
    note: str | None = None
    counts: list[CashCount] = field(default_factory=list)

    def close(
        self,
        counts: list[CashCount],
        now: datetime,
        closed_by: str,
        note: str | None = None,
    ) -> None:
        if self.status is CashSessionStatus.CLOSED:
            raise CashSessionAlreadyClosed()
        self.counts = counts
        self.closed_at = now
        self.closed_by = closed_by
        self.note = note
        self.status = CashSessionStatus.CLOSED
