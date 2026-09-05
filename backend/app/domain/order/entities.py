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
    NoCourseToFire,
)
from app.domain.order.value_objects import (
    Course,
    CourseState,
    ItemStatus,
    OrderSource,
    OrderStatus,
    SelectedOption,
    Station,
)
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
    # Tiempo de servicio (copiado del producto al cargar; el mozo lo puede
    # cambiar por línea mientras no esté al fuego).
    course: Course = Course.MAIN
    sent_at: datetime | None = None
    ready_at: datetime | None = None
    # Modificadores elegidos (Carta QR F2 D). Display-only: el price_delta ya está
    # sumado en unit_price. Vacío → paridad (ítem sin opciones). Snapshot al pedir.
    selected_options: list[SelectedOption] = field(default_factory=list)

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
    # table_sessions (cimiento): la comanda cuelga de la sesión de mesa (1:N). None
    # en órdenes previas → fallback al comportamiento actual (paridad).
    session_id: str | None = None
    # CRM: cliente atribuido a la comanda (para el historial de compras). None → sin
    # atribuir (no cuenta a ningún cliente; nada se infla).
    customer_id: str | None = None
    # Origen de la comanda (Carta QR F2). WAITER por default → paridad; CUSTOMER_QR
    # = la cargó el comensal desde el QR.
    source: OrderSource = OrderSource.WAITER

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

    def march(
        self, now: datetime | None = None, *, coursing: bool = True
    ) -> list[OrderItem]:
        """Send the PENDING plates to the kitchen/bar. Returns the plates that
        actually hit the fire (SENT) so the caller can notify their stations.

        With ``coursing`` (the waiter's flow): IMMEDIATE plates (bar) and the
        course due now go SENT; later courses go HELD — the kitchen sees them
        (mise en place) and cooks them when the waiter fires that course. The
        course due now is the lowest pending course, unless a lower course is
        still in flight (then it waits its turn: no cold mains while the table
        eats the starter). Empty courses are simply skipped. Without coursing
        (QR / batch: nobody paces the table) everything fires, as before."""
        if self.status in (OrderStatus.PAID, OrderStatus.CANCELLED):
            raise InvalidOrderTransition()
        pending = [it for it in self.items if it.status is ItemStatus.PENDING]
        if not pending:
            raise EmptyOrder()
        if not coursing:
            return self._fire(pending, now)
        active = self.active_course()
        pending_courses = sorted(
            {it.course for it in pending if it.course.coursed},
            key=lambda c: c.sequence,
        )
        due: Course | None = None
        if pending_courses:
            lowest = pending_courses[0]
            if active is None or lowest.sequence <= active.sequence:
                due = lowest
        fired: list[OrderItem] = []
        for it in pending:
            if not it.course.coursed or it.course is due:
                fired.append(it)
            else:
                it.status = ItemStatus.HELD
        # A course that becomes due fires along its plates held from an earlier round.
        if due is not None:
            fired += [
                it
                for it in self.items
                if it.status is ItemStatus.HELD and it.course is due
            ]
        if not fired:
            self._recompute_status()  # everything went on hold: still "marchado"
            return []
        return self._fire(fired, now)

    def fire_next_course(self, now: datetime | None = None) -> list[OrderItem]:
        """"Marchar principales": fire the lowest held course — the waiter saw
        the table finish the previous one. Pending plates of that same course
        ride along (no orphan line the waiter forgot to march)."""
        if self.status in (OrderStatus.PAID, OrderStatus.CANCELLED):
            raise InvalidOrderTransition()
        course = self.next_held_course()
        if course is None:
            raise NoCourseToFire()
        targets = [
            it
            for it in self.items
            if it.course is course
            and it.status in (ItemStatus.HELD, ItemStatus.PENDING)
        ]
        return self._fire(targets, now)

    def fire_all(self, now: datetime | None = None) -> list[OrderItem]:
        """"Marchar todo": every pending/held plate hits the fire now (the table
        wants everything together)."""
        if self.status in (OrderStatus.PAID, OrderStatus.CANCELLED):
            raise InvalidOrderTransition()
        targets = [
            it for it in self.items if it.status in (ItemStatus.PENDING, ItemStatus.HELD)
        ]
        if not targets:
            raise EmptyOrder()
        return self._fire(targets, now)

    def _fire(self, items: list[OrderItem], now: datetime | None) -> list[OrderItem]:
        for it in items:
            it.status = ItemStatus.SENT
            it.sent_at = now
        self._recompute_status()
        return items

    def advance_course(
        self,
        course: Course,
        action: str,
        now: datetime | None = None,
        station: Station | None = None,
    ) -> list[OrderItem]:
        """Bump every plate of a course at once — the KDS "Listo" per course
        (also "preparing" / "served"). ``station`` narrows to one board."""
        if action not in _ITEM_TRANSITIONS or action == "recall":
            raise InvalidItemTransition()
        expected, target = _ITEM_TRANSITIONS[action]
        matching = [
            it
            for it in self.items
            if it.course is course
            and it.status is expected
            and (station is None or it.station is station)
        ]
        if not matching:
            raise InvalidItemTransition()
        for it in matching:
            it.status = target
            if target is ItemStatus.READY:
                it.ready_at = now
        self._recompute_status()
        return matching

    def set_item_course(self, item_id: str, course: Course) -> None:
        """Override a plate's course ("la provoleta como principal") while it
        is not on the fire yet."""
        item = self._find_item(item_id)
        if item.status not in (ItemStatus.PENDING, ItemStatus.HELD):
            raise ItemNotPending()
        item.course = course

    # --- courses: derived, never stored ---------------------------------------

    def _live(self) -> list[OrderItem]:
        return [it for it in self.items if it.status is not ItemStatus.CANCELLED]

    def active_course(self) -> Course | None:
        """Lowest coursed course with plates fired and not yet served: the one
        the kitchen is working on / the table is eating."""
        fired = (ItemStatus.SENT, ItemStatus.PREPARING, ItemStatus.READY)
        courses = {
            it.course for it in self._live() if it.status in fired and it.course.coursed
        }
        return min(courses, key=lambda c: c.sequence) if courses else None

    def next_held_course(self) -> Course | None:
        held = {it.course for it in self._live() if it.status is ItemStatus.HELD}
        return min(held, key=lambda c: c.sequence) if held else None

    def course_state(self, course: Course) -> CourseState | None:
        """Cooking > ready plates > held > pending > served. None = no plates."""
        st = {it.status for it in self._live() if it.course is course}
        if not st:
            return None
        if st & {ItemStatus.SENT, ItemStatus.PREPARING}:
            return CourseState.IN_KITCHEN
        if ItemStatus.READY in st:
            return CourseState.READY
        if ItemStatus.HELD in st:
            return CourseState.HELD
        if ItemStatus.PENDING in st:
            return CourseState.PENDING
        return CourseState.SERVED

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
        # HELD plates are marched (the kitchen has them) but not cooking: they
        # keep the order "in kitchen" and block READY/SERVED until fired.
        elif all(it.status is ItemStatus.SERVED for it in active):
            self.status = OrderStatus.SERVED
        elif all(it.status in (ItemStatus.READY, ItemStatus.SERVED) for it in active):
            self.status = OrderStatus.READY
        elif any(it.status is ItemStatus.PREPARING for it in active):
            self.status = OrderStatus.PREPARING
        else:
            self.status = OrderStatus.SENT
