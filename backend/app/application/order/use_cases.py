from __future__ import annotations

from uuid import uuid4

from app.application.analytics.ports import SalesProjector
from app.application.clock import utcnow
from app.application.inventory.ports import InventoryConsumer
from app.application.order.dtos import BatchOrderItemInput, CreateOrderResult
from app.application.table_session.use_cases import (
    AssignTableWaiter,
    close_session_if_idle,
)
from app.domain.identity.ports import TenantContext
from app.domain.invoice.repository import InvoiceRepository
from app.domain.invoice.value_objects import InvoiceStatus
from app.domain.notification.ports import NotificationService, PushMessage
from app.domain.order.entities import Order, OrderItem
from app.domain.order.exceptions import (
    InvalidOrderTransition,
    OrderHasAuthorizedInvoice,
    OrderNotFound,
    OrderNotFullyPaid,
)
from app.domain.order.repository import OrderRepository
from app.domain.order.value_objects import (
    CUSTOMER_WAITER_ID,
    Course,
    CourseState,
    ItemStatus,
    OrderSource,
    OrderStatus,
    SelectedOption,
    Station,
)
from app.domain.payment.repository import PaymentRepository
from app.domain.payment.value_objects import PaymentDirection, PaymentStatus
from app.domain.product.exceptions import InactiveProduct, ProductNotFound
from app.domain.product.modifier_repository import ModifierRepository
from app.domain.product.modifiers import select_options
from app.domain.product.repository import ProductRepository
from app.domain.realtime.ports import DomainEvent, EventBus
from app.domain.shared.money import Money
from app.domain.table.exceptions import TableNotFound
from app.domain.table.repository import TableRepository
from app.domain.table_session.entities import TableSession
from app.domain.table_session.repository import TableSessionRepository
from app.domain.table_session.value_objects import SessionStatus
from app.domain.tenant.exceptions import TenantNotFound
from app.domain.tenant.repository import TenantRepository


class CreateOrder:
    """Open an order for a table, priced in the tenant's currency.

    Also ensures the table has an open **session** (the visit) and hangs the
    order off it (``session_id``). The session is reused if one is already open
    (a party's second round shares the visit) and created implicitly otherwise,
    so the floor's session-aware view works even without the explicit PAX/waiter
    selector. Parity: this is additive — the order behaves exactly as before."""

    def __init__(
        self,
        orders: OrderRepository,
        tables: TableRepository,
        tenants: TenantRepository,
        sessions: TableSessionRepository,
        tenant_context: TenantContext,
        event_bus: EventBus,
    ) -> None:
        self._orders = orders
        self._tables = tables
        self._tenants = tenants
        self._sessions = sessions
        self._tenant_context = tenant_context
        self._event_bus = event_bus

    async def execute(
        self,
        *,
        tenant_id: str,
        waiter_id: str,
        table_id: str,
        order_id: str | None = None,
        source: OrderSource = OrderSource.WAITER,
    ) -> CreateOrderResult:
        self._tenant_context.set(tenant_id)
        if order_id is not None:
            existing = await self._orders.get_by_id(tenant_id, order_id)
            if existing is not None:
                return CreateOrderResult(order_id=existing.id)  # idempotent no-op
        table = await self._tables.get_by_id(tenant_id, table_id)
        if table is None:
            raise TableNotFound()
        tenant = await self._tenants.get_by_id(tenant_id)
        if tenant is None:
            raise TenantNotFound()
        session = await self._sessions.get_open_by_table(tenant_id, table_id)
        if session is None:
            session = TableSession(
                id=str(uuid4()),
                tenant_id=tenant_id,
                table_id=table_id,
                status=SessionStatus.OPEN,
                pax=table.capacity,
                waiter_id=waiter_id,
                opened_at=utcnow(),
            )
            await self._sessions.add(session)
        order = Order(
            id=order_id or str(uuid4()),
            tenant_id=tenant_id,
            table_id=table_id,
            waiter_id=waiter_id,
            currency=tenant.currency,
            session_id=session.id,
            source=source,
        )
        await self._orders.add(order)
        await self._event_bus.publish(_floor_changed(order))  # table → occupied
        return CreateOrderResult(order_id=order.id)


class GetOrder:
    def __init__(self, orders: OrderRepository, tenant_context: TenantContext) -> None:
        self._orders = orders
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str, order_id: str) -> Order:
        self._tenant_context.set(tenant_id)
        order = await self._orders.get_by_id(tenant_id, order_id)
        if order is None:
            raise OrderNotFound()
        return order


class AddOrderItem:
    """Add a line item to an OPEN order, snapshotting the product name + price.

    ``option_ids`` are the modifier choices ("punto del bife"). ``None`` means
    the client does not do modifiers (legacy waiter flow): a plain line, no
    validation. A list (even empty) means the client knows the groups, so the
    selection is validated against them (required groups enforced) and the
    price deltas are folded into the unit price — same rules as the QR menu."""

    def __init__(
        self,
        orders: OrderRepository,
        products: ProductRepository,
        modifiers: ModifierRepository,
        tenant_context: TenantContext,
    ) -> None:
        self._orders = orders
        self._products = products
        self._modifiers = modifiers
        self._tenant_context = tenant_context

    async def execute(
        self,
        *,
        tenant_id: str,
        order_id: str,
        product_id: str,
        quantity: int,
        note: str | None,
        item_id: str | None = None,
        option_ids: list[str] | None = None,
        course: Course | None = None,
    ) -> Order:
        self._tenant_context.set(tenant_id)
        order = await self._orders.get_by_id(tenant_id, order_id)
        if order is None:
            raise OrderNotFound()
        if item_id is not None and any(it.id == item_id for it in order.items):
            return order  # idempotent no-op (retry/replay of an item already added)
        product = await self._products.get_by_id(tenant_id, product_id)
        if product is None:
            raise ProductNotFound()
        if not product.active:
            raise InactiveProduct()
        selected: list[SelectedOption] = []
        unit_price = product.price
        if option_ids is not None:
            groups = await self._modifiers.list_for_product(tenant_id, product_id)
            chosen = select_options(groups, option_ids)  # InvalidModifierSelection
            selected = [SelectedOption(o.id, o.name, o.price_delta) for o in chosen]
            # Delta folded into unit_price (money math reads one number);
            # the list is the kitchen-ticket snapshot. Mirrors AddOrderItemsBatch.
            delta = sum(o.price_delta for o in chosen)
            unit_price = Money(product.price.amount + delta, product.price.currency)
        order.add_item(
            OrderItem(
                id=item_id or str(uuid4()),
                product_id=product.id,
                name=product.name,
                unit_price=unit_price,
                quantity=quantity,
                note=note,
                station=product.station,
                # Curso del plato (de la carta) salvo override por línea.
                course=course or product.effective_course,
                selected_options=selected,
            )
        )
        await self._orders.save(order)
        return order


class RemoveOrderItem:
    """Remove a line item from an order that is still OPEN."""

    def __init__(self, orders: OrderRepository, tenant_context: TenantContext) -> None:
        self._orders = orders
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str, order_id: str, item_id: str) -> Order:
        self._tenant_context.set(tenant_id)
        order = await self._orders.get_by_id(tenant_id, order_id)
        if order is None:
            raise OrderNotFound()
        order.remove_item(item_id)
        await self._orders.save(order)
        return order


class SetItemQuantity:
    """Change a line item's quantity while the order is still OPEN."""

    def __init__(self, orders: OrderRepository, tenant_context: TenantContext) -> None:
        self._orders = orders
        self._tenant_context = tenant_context

    async def execute(
        self, *, tenant_id: str, order_id: str, item_id: str, quantity: int
    ) -> Order:
        self._tenant_context.set(tenant_id)
        order = await self._orders.get_by_id(tenant_id, order_id)
        if order is None:
            raise OrderNotFound()
        order.set_item_quantity(item_id, quantity)
        await self._orders.save(order)
        return order


class SetItemNote:
    """Set (or clear) the kitchen note of a line item while it is still
    PENDING — "how the dish is wanted" (no salt, well done). Once marched the
    note is frozen: the kitchen already read it."""

    def __init__(self, orders: OrderRepository, tenant_context: TenantContext) -> None:
        self._orders = orders
        self._tenant_context = tenant_context

    async def execute(
        self, *, tenant_id: str, order_id: str, item_id: str, note: str | None
    ) -> Order:
        self._tenant_context.set(tenant_id)
        order = await self._orders.get_by_id(tenant_id, order_id)
        if order is None:
            raise OrderNotFound()
        order.set_item_note(item_id, note)
        await self._orders.save(order)
        return order


class AddOrderItemsBatch:
    """Add several line items (and optionally send) in a single transaction.

    Each line carries an optional client-generated id, so a retry/replay is an
    idempotent no-op. This is what lets the waiter assemble a whole comanda
    (offline if needed) and persist it in one round-trip without duplicating.
    """

    def __init__(
        self,
        orders: OrderRepository,
        products: ProductRepository,
        tenant_context: TenantContext,
        event_bus: EventBus,
    ) -> None:
        self._orders = orders
        self._products = products
        self._tenant_context = tenant_context
        self._event_bus = event_bus

    async def execute(
        self,
        *,
        tenant_id: str,
        order_id: str,
        items: list[BatchOrderItemInput],
        send: bool = False,
    ) -> Order:
        self._tenant_context.set(tenant_id)
        order = await self._orders.get_by_id(tenant_id, order_id)
        if order is None:
            raise OrderNotFound()
        seen = {it.id for it in order.items}
        for line in items:
            if line.item_id is not None and line.item_id in seen:
                continue  # idempotent no-op for this line
            product = await self._products.get_by_id(tenant_id, line.product_id)
            if product is None:
                raise ProductNotFound()
            if not product.active:
                raise InactiveProduct()
            new_id = line.item_id or str(uuid4())
            # Modificadores: el price_delta se pliega en el unit_price (así toda la
            # matemática — sale_facts/finanzas/factura — sigue leyendo un solo
            # número); la lista queda como snapshot para el ticket de cocina.
            delta = sum(o.price_delta for o in line.selected_options)
            unit_price = Money(product.price.amount + delta, product.price.currency)
            order.add_item(
                OrderItem(
                    id=new_id,
                    product_id=product.id,
                    name=product.name,
                    unit_price=unit_price,
                    quantity=line.quantity,
                    note=line.note,
                    station=product.station,
                    course=product.effective_course,
                    selected_options=list(line.selected_options),
                )
            )
            seen.add(new_id)
        marched: list[OrderItem] = []
        # Guard keeps the batch idempotent: a replay (no new PENDING items) must
        # not raise EmptyOrder on the already-marched order.
        if send and any(it.status is ItemStatus.PENDING for it in order.items):
            # Carta QR / batch: nadie marca el ritmo de la mesa → todo al fuego.
            marched = order.march(utcnow(), coursing=False)
        await self._orders.save(order)
        await self._event_bus.publish(_floor_changed(order))
        for event in _kds_changed(order, {it.station for it in marched}):
            await self._event_bus.publish(event)
        return order


def _kds_changed(order: Order, stations: set[Station]) -> list[DomainEvent]:
    """'Refetch the KDS board' signals — one per affected station. Carries no
    data, just ids/station, so tenant isolation never depends on the stream."""
    return [
        DomainEvent(
            type="kds.changed",
            tenant_id=order.tenant_id,
            payload={"order_id": order.id, "station": station.value},
        )
        for station in stations
    ]


def _floor_changed(order: Order) -> DomainEvent:
    """A 'refetch the floor' signal — a table's occupancy/total changed."""
    return _floor_changed_table(order.tenant_id, order.table_id)


def _floor_changed_table(tenant_id: str, table_id: str) -> DomainEvent:
    return DomainEvent(
        type="floor.changed",
        tenant_id=tenant_id,
        payload={"table_id": table_id},
    )


# Concordancia del "listo/a(s)" con la etiqueta del curso.
_READY_WORD: dict[Course, str] = {Course.MAIN: "listos", Course.IMMEDIATE: "listas"}

_COURSE_LABEL_ES: dict[Course, str] = {
    Course.IMMEDIATE: "bebidas",
    Course.STARTER: "entrada",
    Course.MAIN: "principales",
    Course.DESSERT: "postre",
}


def _order_ready(order: Order, table_number: str, course: Course) -> DomainEvent:
    """Signal the owning waiter that a COURSE is ready to serve (every fired plate
    of that course READY). ``waiter_id`` lets the client deliver it only to the
    order's owner. Additive payload: clients that ignore ``course`` keep working."""
    return DomainEvent(
        type="order.ready",
        tenant_id=order.tenant_id,
        payload={
            "order_id": order.id,
            "table_id": order.table_id,
            "table_number": table_number,
            "waiter_id": order.waiter_id or "",
            "course": course.value,
            "course_label": _COURSE_LABEL_ES[course],
        },
    )


def _course_items_line(order: Order, course: Course, limit: int = 4) -> str:
    """"1× Provoleta · 1× Rabas": lo que hay que llevar de ESE curso."""
    live = [
        it
        for it in order.items
        if it.course is course and it.status is ItemStatus.READY
    ]
    parts = [f"{it.quantity}× {it.name}" for it in live[:limit]]
    line = " · ".join(parts)
    if len(live) > limit:
        line += f" +{len(live) - limit}"
    return line


def _items_line(order: Order, limit: int = 4) -> str:
    """Resumen legible de lo que hay que llevar: "2× Milanesa · 1× Ensalada"
    (para el cuerpo del push, así el mozo sabe qué agarrar sin abrir la app)."""
    live = [it for it in order.items if it.status is not ItemStatus.CANCELLED]
    parts = [f"{it.quantity}× {it.name}" for it in live[:limit]]
    line = " · ".join(parts)
    if len(live) > limit:
        line += f" +{len(live) - limit}"
    return line


async def _notify_order_ready(
    notifications: NotificationService,
    order: Order,
    table_number: str,
    course: Course,
) -> None:
    """Push "Mesa N · entrada lista" con los platos de ese curso al mozo dueño
    (Fase 4), en paralelo al SSE. Salta si la orden no tiene dueño real."""
    if not order.waiter_id or order.waiter_id == CUSTOMER_WAITER_ID:
        return
    what = _COURSE_LABEL_ES[course]
    ready = _READY_WORD.get(course, "lista")
    title = f"Mesa {table_number} · {what} {ready}" if table_number else f"Comanda · {what} {ready}"
    body = _course_items_line(order, course) or "Tu comanda está lista."
    await notifications.notify_user(
        tenant_id=order.tenant_id,
        user_id=order.waiter_id,
        message=PushMessage(
            title=title,
            body=body,
            data={
                "kind": "order.ready",
                "order_id": order.id,
                "table_number": table_number,
                "course": course.value,
            },
        ),
    )


class SendOrder:
    """March an order to the kitchen (PENDING→SENT). Confirming a QR order goes
    through here: the waiter who marches it becomes the table's owner (Fase 2),
    but only if the table is still orphan — a table already owned is left as is."""

    def __init__(
        self,
        orders: OrderRepository,
        assign_waiter: AssignTableWaiter,
        tenant_context: TenantContext,
        event_bus: EventBus,
    ) -> None:
        self._orders = orders
        self._assign_waiter = assign_waiter
        self._tenant_context = tenant_context
        self._event_bus = event_bus

    async def execute(
        self,
        *,
        tenant_id: str,
        order_id: str,
        waiter_id: str | None = None,
        coursing: bool = True,
    ) -> Order:
        self._tenant_context.set(tenant_id)
        order = await self._orders.get_by_id(tenant_id, order_id)
        if order is None:
            raise OrderNotFound()
        # Estaciones de TODO lo marchado (al fuego o en espera): la cocina tiene
        # que ver el curso que viene aunque todavía no lo cocine.
        touched = {it.station for it in order.items if it.status is ItemStatus.PENDING}
        marched = order.march(utcnow(), coursing=coursing)
        await self._orders.save(order)
        # Confirmar = quedar dueño de la mesa huérfana (Caso B). No roba una mesa
        # que ya tiene dueño; y estampa las órdenes vivas (para el aviso "listo").
        if waiter_id and order.session_id:
            await self._assign_waiter.execute(
                tenant_id=tenant_id,
                session_id=order.session_id,
                waiter_id=waiter_id,
                only_if_unassigned=True,
                conflict_raises=False,
            )
            order = await self._orders.get_by_id(tenant_id, order_id) or order
        del marched  # lo que se notifica es `touched` (fuego + espera)
        for event in _kds_changed(order, touched):
            await self._event_bus.publish(event)
        await self._event_bus.publish(_floor_changed(order))
        return order


class FireNextCourse:
    """"Marchar principales": the waiter saw the table finish the previous
    course → the lowest held course hits the fire."""

    def __init__(
        self, orders: OrderRepository, tenant_context: TenantContext, event_bus: EventBus
    ) -> None:
        self._orders = orders
        self._tenant_context = tenant_context
        self._event_bus = event_bus

    async def execute(self, *, tenant_id: str, order_id: str) -> Order:
        self._tenant_context.set(tenant_id)
        order = await self._orders.get_by_id(tenant_id, order_id)
        if order is None:
            raise OrderNotFound()
        fired = order.fire_next_course(utcnow())
        await self._orders.save(order)
        for event in _kds_changed(order, {it.station for it in fired}):
            await self._event_bus.publish(event)
        await self._event_bus.publish(_floor_changed(order))
        return order


class FireAllCourses:
    """"Marchar todo": every pending / held plate hits the fire now."""

    def __init__(
        self, orders: OrderRepository, tenant_context: TenantContext, event_bus: EventBus
    ) -> None:
        self._orders = orders
        self._tenant_context = tenant_context
        self._event_bus = event_bus

    async def execute(self, *, tenant_id: str, order_id: str) -> Order:
        self._tenant_context.set(tenant_id)
        order = await self._orders.get_by_id(tenant_id, order_id)
        if order is None:
            raise OrderNotFound()
        fired = order.fire_all(utcnow())
        await self._orders.save(order)
        for event in _kds_changed(order, {it.station for it in fired}):
            await self._event_bus.publish(event)
        await self._event_bus.publish(_floor_changed(order))
        return order


class SetItemCourse:
    """Override a plate's course ("la provoleta como principal") before it
    hits the fire."""

    def __init__(self, orders: OrderRepository, tenant_context: TenantContext) -> None:
        self._orders = orders
        self._tenant_context = tenant_context

    async def execute(
        self, *, tenant_id: str, order_id: str, item_id: str, course: Course
    ) -> Order:
        self._tenant_context.set(tenant_id)
        order = await self._orders.get_by_id(tenant_id, order_id)
        if order is None:
            raise OrderNotFound()
        order.set_item_course(item_id, course)
        await self._orders.save(order)
        return order


class AdvanceCourse:
    """Bump a whole course at once — the KDS "Listo" per course (also
    "preparing" / "served"). Publishes the course-ready signal + push when the
    course completes: "Mesa 4 · entrada lista"."""

    def __init__(
        self,
        orders: OrderRepository,
        tables: TableRepository,
        tenant_context: TenantContext,
        event_bus: EventBus,
        notifications: NotificationService,
    ) -> None:
        self._orders = orders
        self._tables = tables
        self._tenant_context = tenant_context
        self._event_bus = event_bus
        self._notifications = notifications

    async def execute(
        self,
        *,
        tenant_id: str,
        order_id: str,
        course: Course,
        action: str,
        station: Station | None = None,
    ) -> Order:
        self._tenant_context.set(tenant_id)
        order = await self._orders.get_by_id(tenant_id, order_id)
        if order is None:
            raise OrderNotFound()
        moved = order.advance_course(course, action, utcnow(), station=station)
        await self._orders.save(order)
        for event in _kds_changed(order, {it.station for it in moved}):
            await self._event_bus.publish(event)
        await self._event_bus.publish(_floor_changed(order))
        if action == "ready":
            await _publish_course_ready(
                self._tables, self._event_bus, self._notifications, tenant_id, order, course
            )
        return order


async def _publish_course_ready(
    tables: TableRepository,
    event_bus: EventBus,
    notifications: NotificationService,
    tenant_id: str,
    order: Order,
    course: Course,
) -> None:
    """Emit once, when the LAST plate of the course flips it to READY."""
    if order.course_state(course) is not CourseState.READY:
        return
    table = await tables.get_by_id(tenant_id, order.table_id)
    number = str(table.number) if table is not None else ""
    await event_bus.publish(_order_ready(order, number, course))
    await _notify_order_ready(notifications, order, number, course)


class AdvanceItem:
    """Bump (or recall) a single item along its kitchen lifecycle. This is what
    the per-station KDS board uses to mark items ready one by one."""

    def __init__(
        self,
        orders: OrderRepository,
        tables: TableRepository,
        tenant_context: TenantContext,
        event_bus: EventBus,
        notifications: NotificationService,
    ) -> None:
        self._orders = orders
        self._tables = tables
        self._tenant_context = tenant_context
        self._event_bus = event_bus
        self._notifications = notifications

    async def execute(
        self, *, tenant_id: str, order_id: str, item_id: str, action: str
    ) -> Order:
        self._tenant_context.set(tenant_id)
        order = await self._orders.get_by_id(tenant_id, order_id)
        if order is None:
            raise OrderNotFound()
        item = order.advance_item(item_id, action, utcnow())
        await self._orders.save(order)
        for event in _kds_changed(order, {item.station}):
            await self._event_bus.publish(event)
        await self._event_bus.publish(_floor_changed(order))
        if action == "ready":
            # El último plato del curso lo deja READY → aviso una sola vez.
            await _publish_course_ready(
                self._tables,
                self._event_bus,
                self._notifications,
                tenant_id,
                order,
                item.course,
            )
        return order


class AdvanceOrder:
    """Advance a whole order's lifecycle (preparing/ready/served/cancel).

    A convenience that moves every matching item at once; the per-item board uses
    ``AdvanceItem`` instead.
    """

    def __init__(
        self,
        orders: OrderRepository,
        tables: TableRepository,
        tenant_context: TenantContext,
        event_bus: EventBus,
        notifications: NotificationService,
        sessions: TableSessionRepository | None = None,
    ) -> None:
        self._orders = orders
        self._tables = tables
        self._tenant_context = tenant_context
        self._event_bus = event_bus
        self._notifications = notifications
        self._sessions = sessions

    async def execute(self, *, tenant_id: str, order_id: str, action: str) -> Order:
        self._tenant_context.set(tenant_id)
        order = await self._orders.get_by_id(tenant_id, order_id)
        if order is None:
            raise OrderNotFound()
        if action == "preparing":
            order.start_preparing()
        elif action == "ready":
            order.mark_ready(utcnow())
        elif action == "served":
            order.mark_served()
        elif action == "cancel":
            order.cancel()
        else:
            raise InvalidOrderTransition()
        await self._orders.save(order)
        if action == "cancel" and self._sessions is not None:
            # Última orden viva anulada → la visita terminó: la mesa vuelve a libre.
            await close_session_if_idle(
                self._sessions, self._orders, tenant_id, order.table_id, utcnow()
            )
        for event in _kds_changed(order, {it.station for it in order.items}):
            await self._event_bus.publish(event)
        await self._event_bus.publish(_floor_changed(order))
        if action == "ready":
            # "Listo" de toda la orden: avisar por cada curso que quedó listo.
            for course in {it.course for it in order.items}:
                await _publish_course_ready(
                    self._tables,
                    self._event_bus,
                    self._notifications,
                    tenant_id,
                    order,
                    course,
                )
        return order


class TransferOrder:
    """Move an active order to another (existing) table."""

    def __init__(
        self,
        orders: OrderRepository,
        tables: TableRepository,
        tenant_context: TenantContext,
        event_bus: EventBus,
    ) -> None:
        self._orders = orders
        self._tables = tables
        self._tenant_context = tenant_context
        self._event_bus = event_bus

    async def execute(self, *, tenant_id: str, order_id: str, table_id: str) -> Order:
        self._tenant_context.set(tenant_id)
        order = await self._orders.get_by_id(tenant_id, order_id)
        if order is None:
            raise OrderNotFound()
        if table_id == order.table_id:
            return order  # already there — no-op
        if await self._tables.get_by_id(tenant_id, table_id) is None:
            raise TableNotFound()
        old_table_id = order.table_id
        order.transfer_to(table_id)
        await self._orders.save(order)
        await self._event_bus.publish(_floor_changed_table(tenant_id, old_table_id))
        await self._event_bus.publish(_floor_changed(order))  # new table
        return order


class MergeOrders:
    """Merge a source order into a destination order (two tables joined). The
    source is emptied and closed; the destination is billed for everything."""

    def __init__(
        self,
        orders: OrderRepository,
        tenant_context: TenantContext,
        event_bus: EventBus,
    ) -> None:
        self._orders = orders
        self._tenant_context = tenant_context
        self._event_bus = event_bus

    async def execute(
        self, *, tenant_id: str, destination_order_id: str, source_order_id: str
    ) -> Order:
        self._tenant_context.set(tenant_id)
        if destination_order_id == source_order_id:
            raise InvalidOrderTransition()
        destination = await self._orders.get_by_id(tenant_id, destination_order_id)
        source = await self._orders.get_by_id(tenant_id, source_order_id)
        if destination is None or source is None:
            raise OrderNotFound()
        source_table_id = source.table_id
        stations = {it.station for it in source.items}
        destination.merge_from(source)
        # Save the emptied source first so its item rows are gone before the same
        # items are re-inserted under the destination (shared ids, no collision).
        await self._orders.save(source)
        await self._orders.save(destination)
        await self._event_bus.publish(_floor_changed_table(tenant_id, source_table_id))
        await self._event_bus.publish(_floor_changed(destination))
        for event in _kds_changed(destination, stations):
            await self._event_bus.publish(event)
        return destination


class ReopenOrder:
    """Re-open a PAID order so the cashier can correct it, reversing the sale's
    side-effects. Blocked when the comanda already has an AFIP-authorized
    comprobante (a CAE can't be silently undone — that needs a nota de crédito).

    The reversals run before the state flips and are each idempotent (drop the
    sale_facts, credit the consumed stock back, drop the SALE movements), so a
    retry — or the re-pay that follows — re-runs them cleanly. Money already
    collected (the payments) is left untouched: refunding is the cashier's
    separate call (anular/reembolsar)."""

    def __init__(
        self,
        orders: OrderRepository,
        invoices: InvoiceRepository,
        inventory: InventoryConsumer,
        sales: SalesProjector,
        tenant_context: TenantContext,
        event_bus: EventBus,
    ) -> None:
        self._orders = orders
        self._invoices = invoices
        self._inventory = inventory
        self._sales = sales
        self._tenant_context = tenant_context
        self._event_bus = event_bus

    async def execute(self, *, tenant_id: str, order_id: str) -> Order:
        self._tenant_context.set(tenant_id)
        order = await self._orders.get_by_id(tenant_id, order_id)
        if order is None:
            raise OrderNotFound()
        if order.status is not OrderStatus.PAID:
            return order  # idempotent no-op: only a PAID order reopens
        invoice = await self._invoices.get_by_order(tenant_id, order_id)
        if invoice is not None and invoice.status is InvoiceStatus.AUTHORIZED:
            raise OrderHasAuthorizedInvoice()
        await self._inventory.reverse_for_order(tenant_id, order_id)
        await self._sales.reverse_order(tenant_id, order_id)
        order.reopen()
        await self._orders.save(order)
        await self._event_bus.publish(_floor_changed(order))  # table re-occupied
        return order


class ListOrders:
    def __init__(self, orders: OrderRepository, tenant_context: TenantContext) -> None:
        self._orders = orders
        self._tenant_context = tenant_context

    async def execute(
        self, *, tenant_id: str, status: OrderStatus | None = None
    ) -> list[Order]:
        self._tenant_context.set(tenant_id)
        return await self._orders.list_by_status(tenant_id, status)


class GetKdsOrders:
    def __init__(self, orders: OrderRepository, tenant_context: TenantContext) -> None:
        self._orders = orders
        self._tenant_context = tenant_context

    async def execute(
        self, *, tenant_id: str, station: Station | None = None
    ) -> list[Order]:
        self._tenant_context.set(tenant_id)
        return await self._orders.list_kds(tenant_id, station)


class ListPendingQrOrders:
    """The "QR por confirmar" tray: orders a diner placed by QR that are still
    OPEN (not marched to the kitchen). A waiter confirms one via ``SendOrder``."""

    def __init__(self, orders: OrderRepository, tenant_context: TenantContext) -> None:
        self._orders = orders
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str) -> list[Order]:
        self._tenant_context.set(tenant_id)
        return await self._orders.list_pending_qr(tenant_id)


class CloseSettledOrder:
    """Free the table of an order that's ALREADY fully paid — "Liberar mesa".

    Self-service (Fase 3): the diner paid up front, so the order isn't marked PAID
    when served (that would free the table while they're still eating). When they
    leave, staff frees it: this marks the order PAID (it drops off the floor's
    active list). Refuses (``OrderNotFullyPaid``) if there's still a balance, so a
    table with an unpaid order can never be freed by mistake — use the normal cobro."""

    def __init__(
        self,
        orders: OrderRepository,
        payments: PaymentRepository,
        tenant_context: TenantContext,
        event_bus: EventBus,
        sessions: TableSessionRepository | None = None,
    ) -> None:
        self._orders = orders
        self._payments = payments
        self._tenant_context = tenant_context
        self._event_bus = event_bus
        self._sessions = sessions

    async def execute(self, *, tenant_id: str, order_id: str) -> Order:
        self._tenant_context.set(tenant_id)
        order = await self._orders.get_by_id(tenant_id, order_id)
        if order is None:
            raise OrderNotFound()
        if order.status in (OrderStatus.PAID, OrderStatus.CANCELLED):
            raise InvalidOrderTransition()
        confirmed = await self._payments.list_by_order(tenant_id, order_id)
        paid = sum(
            p.amount.amount
            for p in confirmed
            if p.direction is PaymentDirection.INFLOW
            and p.status is PaymentStatus.CONFIRMED
        )
        if paid < order.total().amount:
            raise OrderNotFullyPaid()
        order.mark_paid()
        await self._orders.save(order)
        if self._sessions is not None:
            await close_session_if_idle(
                self._sessions, self._orders, tenant_id, order.table_id, utcnow()
            )
        await self._event_bus.publish(_floor_changed(order))
        return order
