from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class CashReportLine:
    """Arqueo line for one payment method (amounts in minor units). ``counted``
    and ``difference`` are None while the session is still OPEN. ``tips`` is the
    propina component already included in ``expected`` (shown so it can be set
    aside for the staff)."""

    method: str
    expected: int
    tips: int
    counted: int | None
    difference: int | None


@dataclass(frozen=True)
class CashMovementRow:
    """A manual cash-drawer movement inside the session (sangría / ingreso /
    pago). ``signed_amount`` is its effect on the drawer cash (+in / −out)."""

    id: str
    kind: str
    amount: int
    signed_amount: int
    reason: str | None
    created_at: datetime | None


@dataclass(frozen=True)
class CashReport:
    """The arqueo Z: per-method esperado vs contado for a register session."""

    session_id: str
    status: str
    currency: str
    opening_float: int
    opened_at: datetime | None
    closed_at: datetime | None
    lines: list[CashReportLine]
    expected_total: int
    counted_total: int | None
    difference_total: int | None
    tips_total: int
    # Movimientos manuales de cajón (ya reflejados en el esperado de CASH).
    movements: list[CashMovementRow] = field(default_factory=list)
    cash_in_total: int = 0  # Σ ingresos de efectivo
    cash_out_total: int = 0  # Σ sangrías + pagos en efectivo
