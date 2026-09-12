from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime

from app.domain.order.entities import Order
from app.domain.order.value_objects import ItemStatus, OrderStatus
from app.domain.table_session.entities import TableSession
from app.domain.table_session.value_objects import SessionStatus

# Orders that no longer occupy the table (their items don't count for the floor).
_TERMINAL_ORDER_STATUSES = (OrderStatus.PAID, OrderStatus.CANCELLED)


@dataclass(frozen=True)
class DerivedSessionState:
    """The LIVE state of a table session, derived on read from its orders' item
    timestamps + the session's human signals. ``since`` anchors the floor timer:
    "how long has the table been waiting in THIS state" (not since it opened)."""

    status: SessionStatus
    since: datetime | None


def _active_items(orders: Iterable[Order]) -> list:
    items = []
    for order in orders:
        if order.status in _TERMINAL_ORDER_STATUSES:
            continue
        items.extend(it for it in order.items if it.status is not ItemStatus.CANCELLED)
    return items


def derive_session_state(
    session: TableSession, orders: Iterable[Order]
) -> DerivedSessionState:
    """Roll the session's orders up to a single floor state, with the "whoever
    needs a human wins" precedence the salon spec asks for (§4.2):

        para_servir (MÁXIMA PRIORIDAD) > a_cobrar > en_cocina > servida > abierta

    Deliberately diverges from ``Order._recompute_status`` in the mixed case: a
    single dish ready to run beats the rest still cooking (that dish is getting
    cold — it needs a human now). For a single-order session with no mixing, it
    matches the current order rollup (parity)."""
    items = _active_items(orders)
    opened = session.opened_at

    ready = [it for it in items if it.status is ItemStatus.READY]
    if ready:
        readies = [it.ready_at for it in ready if it.ready_at is not None]
        return DerivedSessionState(SessionStatus.TO_SERVE, min(readies) if readies else opened)

    # "A cobrar" solo tiene sentido si hay algo que cobrar: una mesa sin ítems
    # (se pidió la cuenta por error, o se anuló/pagó todo) vuelve a "abierta"
    # en vez de quedar trabada pidiendo un cobro de $0.
    if session.bill_requested_at is not None and items:
        return DerivedSessionState(SessionStatus.TO_CHARGE, session.bill_requested_at)

    in_kitchen = [
        it for it in items if it.status in (ItemStatus.SENT, ItemStatus.PREPARING)
    ]
    if in_kitchen:
        sents = [it.sent_at for it in in_kitchen if it.sent_at is not None]
        return DerivedSessionState(SessionStatus.IN_KITCHEN, min(sents) if sents else opened)

    if items and all(it.status is ItemStatus.SERVED for it in items):
        # No per-item served_at is tracked; the meal-in-progress timer runs from
        # when the table opened (good enough — the action moment is a_cobrar).
        return DerivedSessionState(SessionStatus.SERVED, opened)

    return DerivedSessionState(SessionStatus.OPEN, opened)
