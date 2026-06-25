from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CreateOrderResult:
    order_id: str


@dataclass(frozen=True)
class BatchOrderItemInput:
    """One line of a batch add. ``item_id`` (client-generated) makes it idempotent."""

    product_id: str
    quantity: int
    note: str | None = None
    item_id: str | None = None
