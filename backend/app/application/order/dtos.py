from __future__ import annotations

from dataclasses import dataclass, field

from app.domain.order.value_objects import SelectedOption


@dataclass(frozen=True)
class CreateOrderResult:
    order_id: str


@dataclass(frozen=True)
class BatchOrderItemInput:
    """One line of a batch add. ``item_id`` (client-generated) makes it idempotent.

    ``selected_options`` are the modifier choices, already resolved server-side
    (id + name + price_delta) — the delta gets folded into the item's unit price.
    Empty → a plain line (parity with the waiter flow)."""

    product_id: str
    quantity: int
    note: str | None = None
    item_id: str | None = None
    selected_options: list[SelectedOption] = field(default_factory=list)
