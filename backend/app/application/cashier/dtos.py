from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CashReportLine:
    """Arqueo line for one payment method (amounts in minor units). ``counted``
    and ``difference`` are None while the session is still OPEN."""

    method: str
    expected: int
    counted: int | None
    difference: int | None


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
