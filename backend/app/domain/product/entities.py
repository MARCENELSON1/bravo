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
    # QR menu enrichment (Carta QR F2). Photo + description shown to the diner.
    image_url: str | None = None
    description: str | None = None
    # Daily availability ("86'd"): temporarily out today, distinct from ``active``
    # (a permanent delisting). Defaults True → parity for every existing product.
    available_today: bool = True
    created_at: datetime | None = None

    def deactivate(self) -> None:
        self.active = False

    def set_availability(self, available: bool) -> None:
        """Flip today's availability (the "86'd" toggle). Does not touch ``active``."""
        self.available_today = available

    def change_price(self, new_amount: int) -> None:
        """Reprice in the tenant's currency (keeps the money's currency)."""
        self.price = Money(new_amount, self.price.currency)
