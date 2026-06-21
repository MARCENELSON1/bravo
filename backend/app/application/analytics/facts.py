"""Canonical (silver) facts: a normalized, single-shape representation of the
business events the analytics layer reads. Decoupled from how they were captured."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class SaleFact:
    """One line of a PAID order. Snapshots the name/category/price at sale time
    and the recipe food cost when the product has one (else None). Integer minor
    units throughout; ``occurred_at`` is the moment the order was settled (PAID)."""

    id: str
    tenant_id: str
    order_id: str
    order_item_id: str
    product_id: str
    product_name: str
    category: str | None
    quantity: int
    unit_price_amount: int
    line_amount: int
    food_cost_amount: int | None
    currency: str
    waiter_id: str
    table_id: str | None
    occurred_at: datetime
    created_at: datetime | None = None
