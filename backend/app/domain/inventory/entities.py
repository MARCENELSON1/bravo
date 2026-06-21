from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.domain.inventory.costing import is_below_min
from app.domain.inventory.exceptions import InvalidQuantity, InvalidUnitCost
from app.domain.inventory.value_objects import (
    MovementDirection,
    MovementReason,
    UnitOfMeasure,
)
from app.domain.shared.exceptions import CurrencyMismatch
from app.domain.shared.money import Money


@dataclass
class StockMovement:
    """A single change to an ingredient's stock, scoped to a tenant.

    ``qty`` is always a positive integer in milésimas of the base unit; the
    sign of the change is carried by ``direction``. ``order_id`` is set on SALE
    movements (for idempotency), ``unit_cost`` on PURCHASE movements.
    """

    id: str
    tenant_id: str
    ingredient_id: str
    direction: MovementDirection
    reason: MovementReason
    qty: int
    order_id: str | None = None
    unit_cost: Money | None = None
    note: str | None = None
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.qty <= 0:
            raise InvalidQuantity()


@dataclass
class Ingredient:
    """An inventory item (insumo), scoped to a tenant.

    ``stock_qty`` and ``min_qty`` are integers in milésimas of ``unit``;
    ``unit_cost`` is Money per *one* base unit. Stock may go **negative** — a
    sale is never blocked by a shortage, the negative reflects reality and
    raises an alert instead.
    """

    id: str
    tenant_id: str
    name: str
    unit: UnitOfMeasure
    stock_qty: int
    min_qty: int
    unit_cost: Money
    active: bool = True
    created_at: datetime | None = None

    def apply(self, movement: StockMovement) -> None:
        """Add (IN) or subtract (OUT) the movement's quantity from stock.

        OUT can drive ``stock_qty`` below zero on purpose (oversold / a badly
        loaded ingredient) — we never clamp, the shortage is the signal.
        """
        if movement.direction is MovementDirection.IN:
            self.stock_qty += movement.qty
        else:
            self.stock_qty -= movement.qty

    def set_cost(self, unit_cost: Money) -> None:
        """Update the unit cost (last-cost policy, on each purchase)."""
        if unit_cost.amount <= 0:
            raise InvalidUnitCost()
        if unit_cost.currency != self.unit_cost.currency:
            raise CurrencyMismatch()
        self.unit_cost = unit_cost

    @property
    def is_below_min(self) -> bool:
        return is_below_min(self.stock_qty, self.min_qty)


@dataclass
class Supplier:
    """A supplier (proveedor) of ingredients, scoped to a tenant."""

    id: str
    tenant_id: str
    name: str
    contact: str | None = None
    active: bool = True
    created_at: datetime | None = None
