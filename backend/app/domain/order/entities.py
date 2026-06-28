from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from app.domain.order.exceptions import (
    EmptyOrder,
    InvalidItemQuantity,
    InvalidItemTransition,
    InvalidOrderTransition,
    ItemNotFound,
    ItemNotPending,
)
from app.domain.order.value_objects import ItemStatus, OrderStatus, Station
from app.domain.shared.exceptions import CurrencyMismatch
from app.domain.shared.money import Money

# Per-item bump/recall transitions (action → expected, target).
_ITEM_TRANSITIONS: dict[str, tuple[ItemStatus, ItemStatus]] = {
    "preparing": (ItemStatus.SENT, ItemStatus.PREPARING),
    "ready": (ItemStatus.PREPARING, ItemStatus.READY),
    "served": (ItemStatus.READY, ItemStatus.SERVED),
    "recall": (ItemStatus.READY, ItemStatus.PREPARING),  # un-bump a too-early READY
}


@dataclass
class OrderItem:
    """A line item that snapshots the product name + unit price at order time.

    Each item carries its own kitchen lifecycle (``status``) and ``station`` so
    the order can hold multiple rounds and be bumped item by item.
    """

    id: str
    product_id: str
    name: str
    unit_price: Money
    quantity: int
    note: str | None = None
    station: Station = Station.KITCHEN
    status: ItemStatus = ItemStatus.PENDING
    sent_at: datetime | None = None
    ready_at: datetime | None = None

    def line_total(self) -> Money:
        return self.unit_price.times(self.quantity)


@dataclass
class Order:
    """An order (comanda) for a table, scoped to a tenant.

    The order-level ``status`` is *derived* from its items (see
    ``_recompute_status``); PAID/CANCELLED are explicit terminal states. Items
    are added/edited while PENDING, then "marched" (PENDING→SENT) to the KDS and
    advanced per item (SENT→PREPARING→READY→SERVED).
    """

    id: str
    tenant_id: str
    table_id: str
    waiter_id: str
    currency: str
    status: OrderStatus = OrderStatus.OPEN
    items: list[OrderItem] = field(default_factory=list)
    created_at: datetime | None = None

    # --- item editing (only while the item is still PENDING) ----------------

    def add_item(self, item: OrderItem) -> None:
        if self.status in (OrderStatus.PAID, OrderStatus.CANCELLED):
            raise InvalidOrderTransition()
        if item.unit_price.currency != self.currency:
            raise CurrencyMismatch()
        self.items.append(item)
        self._recompute_status()

    def remove_item(self, item_id: str) -> None:
        item = self._find_item(item_id)
        if item.status is not ItemStatus.PENDING:
            raise ItemNotPending()
        self.items.remove(item)
        self._recompute_status()

    def set_item_quantity(self, item_id: str, quantity: int) -> None:
        if quantity < 1:
            raise InvalidItemQuantity()
        item = self._find_item(item_id)
        if item.status is not ItemStatus.PENDING:
            raise ItemNotPending()
        item.quantity = quantity

    def set_item_note(self, item_id: str, note: str | None) -> None:
        item = self._find_item(item_id)
        if item.status is not ItemStatus.PENDING:
            raise ItemNotPending()
        item.note = note

    def _find_item(self, item_id: str) -> OrderItem:
        for item in self.items:
            if item.id == item_id:
                return item
        raise ItemNotFound()

    # --- kitchen lifecycle ---------------------------------------------------

    def march(self, now: datetime | None = None) -> list[OrderItem]:
        """Send the PENDING items to the kitchen/bar (PENDING→SENT). Returns the
        items that were marched (so the caller can notify the right stations)."""
        if self.status in (OrderStatus.PAID, OrderStatus.CANCELLED):
            raise InvalidOrderTransition()
        pending = [it for it in self.items if it.status is ItemStatus.PENDING]
        if not pending:
            raise EmptyOrder()
        for it in pending:
            it.status = ItemStatus.SENT
            it.sent_at = now
        self._recompute_status()
        return pending

    def advance_item(
        self, item_id: str, action: str, now: datetime | None = None
    ) -> OrderItem:
        """Bump (or recall) a single item along its lifecycle."""
        if action not in _ITEM_TRANSITIONS:
            raise InvalidItemTransition()
        expected, target = _ITEM_TRANSITIONS[action]
        item = self._find_item(item_id)
        if item.status is not expected:
            raise InvalidItemTransition()
        item.status = target
        if action == "ready":
            item.ready_at = now
        elif action == "recall":
            item.ready_at = None
        self._recompute_status()
        return item

    # --- order-level lifecycle (backward-compatible whole-order operations) --

    def send_to_kitchen(self, now: datetime | None = None) -> list[OrderItem]:
        return self.march(now)

    def start_preparing(self) -> None:
        self._advance_all(ItemStatus.SENT, ItemStatus.PREPARING)

    def mark_ready(self, now: datetime | None = None) -> None:
        self._advance_all(ItemStatus.PREPARING, ItemStatus.READY, ready_at=now)

    def mark_served(self) -> None:
        self._advance_all(ItemStatus.READY, ItemStatus.SERVED)

    def cancel(self) -> None:
        if self.status in (OrderStatus.SERVED, OrderStatus.CANCELLED):
            raise InvalidOrderTransition()
        self.status = OrderStatus.CANCELLED

    def transfer_to(self, table_id: str) -> None:
        """Move this order to another table (e.g. the party changed seats)."""
        if self.status in (OrderStatus.PAID, OrderStatus.CANCELLED):
            raise InvalidOrderTransition()
        self.table_id = table_id

    def merge_from(self, other: Order) -> None:
        """Absorb another order's items into this one and close the source, so two
        tables that joined are billed together. Item state (status/station/timing)
        is preserved on each moved item."""
        if self.status in (OrderStatus.PAID, OrderStatus.CANCELLED):
            raise InvalidOrderTransition()
        if other.status in (OrderStatus.PAID, OrderStatus.CANCELLED):
            raise InvalidOrderTransition()
        if other.currency != self.currency:
            raise CurrencyMismatch()
        self.items.extend(other.items)
        other.items = []
        other.status = OrderStatus.CANCELLED  # source merged away → frees its table
        self._recompute_status()

    def mark_paid(self) -> None:
        if self.status in (OrderStatus.CANCELLED, OrderStatus.PAID):
            raise InvalidOrderTransition()
        self.status = OrderStatus.PAID

    def reopen(self) -> None:
        """Re-open a settled order so a cashier can correct it (the inverse of
        ``mark_paid``). Only a PAID order reopens; the status is then re-derived
        from its items. The money/projection side-effects (refund, sale_facts,
        stock) are reversed by the caller — the entity only flips the state."""
        if self.status is not OrderStatus.PAID:
            raise InvalidOrderTransition()
        self.status = OrderStatus.SERVED  # leave the terminal state so recompute runs
        self._recompute_status()

    def total(self) -> Money:
        total = Money.zero(self.currency)
        for item in self.items:
            if item.status is ItemStatus.CANCELLED:
                continue
            total = total.plus(item.line_total())
        return total

    def _advance_all(
        self,
        expected: ItemStatus,
        target: ItemStatus,
        ready_at: datetime | None = None,
    ) -> None:
        matching = [it for it in self.items if it.status is expected]
        if not matching:
            raise InvalidOrderTransition()
        for it in matching:
            it.status = target
            if target is ItemStatus.READY:
                it.ready_at = ready_at
        self._recompute_status()

    def _recompute_status(self) -> None:
        """Roll the per-item statuses up to a single order status. PAID/CANCELLED
        are terminal and never derived."""
        if self.status in (OrderStatus.PAID, OrderStatus.CANCELLED):
            return
        active = [it for it in self.items if it.status is not ItemStatus.CANCELLED]
        if not active or all(it.status is ItemStatus.PENDING for it in active):
            self.status = OrderStatus.OPEN
        elif all(it.status is ItemStatus.SERVED for it in active):
            self.status = OrderStatus.SERVED
        elif all(it.status in (ItemStatus.READY, ItemStatus.SERVED) for it in active):
            self.status = OrderStatus.READY
        elif any(it.status is ItemStatus.PREPARING for it in active):
            self.status = OrderStatus.PREPARING
        else:
            self.status = OrderStatus.SENT
