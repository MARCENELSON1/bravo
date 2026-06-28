from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.domain.order.value_objects import Station
from app.domain.shared.money import Money


@dataclass
class Product:
    """A menu product (catalog item), scoped to a tenant."""

    id: str
    tenant_id: str
    name: str
    price: Money
    category: str | None = None
    # Where this product is prepared — snapshotted onto each order item so the
    # KDS can route it to the kitchen or the bar board.
    station: Station = Station.KITCHEN
    active: bool = True
    created_at: datetime | None = None

    def deactivate(self) -> None:
        self.active = False
