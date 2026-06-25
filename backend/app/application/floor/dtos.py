from __future__ import annotations

from dataclasses import dataclass

from app.domain.order.entities import Order
from app.domain.table.entities import Table


@dataclass(frozen=True)
class FloorTable:
    """A table plus its current active order (None → the table is free)."""

    table: Table
    order: Order | None
