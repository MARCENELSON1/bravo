from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from app.domain.order.exceptions import EmptyOrder, InvalidOrderTransition
from app.domain.order.value_objects import OrderStatus
from app.domain.shared.exceptions import CurrencyMismatch
from app.domain.shared.money import Money


@dataclass
class OrderItem:
    """A line item that snapshots the product name + unit price at order time."""

    id: str
    product_id: str
    name: str
    unit_price: Money
    quantity: int
    note: str | None = None

    def line_total(self) -> Money:
        return self.unit_price.times(self.quantity)


@dataclass
class Order:
    """An order (comanda) for a table, scoped to a tenant.

    The lifecycle (OPEN→SENT→PREPARING→READY→SERVED, or CANCELLED) is enforced
    here; the KDS reads SENT/PREPARING orders.
    """

    id: str
    tenant_id: str
    table_id: str
    waiter_id: str
    currency: str
    status: OrderStatus = OrderStatus.OPEN
    items: list[OrderItem] = field(default_factory=list)
    created_at: datetime | None = None

    def add_item(self, item: OrderItem) -> None:
        if self.status is not OrderStatus.OPEN:
            raise InvalidOrderTransition()
        if item.unit_price.currency != self.currency:
            raise CurrencyMismatch()
        self.items.append(item)

    def send_to_kitchen(self) -> None:
        if self.status is not OrderStatus.OPEN:
            raise InvalidOrderTransition()
        if not self.items:
            raise EmptyOrder()
        self.status = OrderStatus.SENT

    def start_preparing(self) -> None:
        self._advance(OrderStatus.SENT, OrderStatus.PREPARING)

    def mark_ready(self) -> None:
        self._advance(OrderStatus.PREPARING, OrderStatus.READY)

    def mark_served(self) -> None:
        self._advance(OrderStatus.READY, OrderStatus.SERVED)

    def cancel(self) -> None:
        if self.status in (OrderStatus.SERVED, OrderStatus.CANCELLED):
            raise InvalidOrderTransition()
        self.status = OrderStatus.CANCELLED

    def total(self) -> Money:
        total = Money.zero(self.currency)
        for item in self.items:
            total = total.plus(item.line_total())
        return total

    def _advance(self, expected: OrderStatus, target: OrderStatus) -> None:
        if self.status is not expected:
            raise InvalidOrderTransition()
        self.status = target
