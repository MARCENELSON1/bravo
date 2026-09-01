from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class TableCallKind(StrEnum):
    """What a diner asked for from the QR menu: the waiter, or the bill."""

    WAITER = "waiter"
    BILL = "bill"


@dataclass(frozen=True)
class TableQrClaims:
    """What a verified table-QR token carries: the tenant whose menu to show and
    the table it was printed for. Self-contained (signed), so a scan resolves the
    tenant without any DB lookup or user session — the token IS the scope."""

    tenant_id: str
    table_id: str
