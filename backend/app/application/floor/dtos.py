from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.domain.order.entities import Order
from app.domain.table.entities import Table
from app.domain.table_session.value_objects import SessionStatus


@dataclass(frozen=True)
class FloorSession:
    """The live view of a table's visit for the floor: its derived state, the
    timestamp that state began (``state_since`` drives the timer), plus who/how
    many. ``None`` on a ``FloorTable`` → the table is free (parity)."""

    id: str
    status: SessionStatus  # derived on read (see derive_session_state)
    state_since: datetime | None
    pax: int | None
    waiter_id: str | None
    waiter_name: str | None
    sector_id: str | None


@dataclass(frozen=True)
class FloorTable:
    """A table plus its current active order (None → the table is free).

    ``session`` is the richer, session-aware view layered on top (state +
    timers + pax); it's additive — ``status``/``order`` keep their meaning so
    any older consumer still works unchanged (parity)."""

    table: Table
    order: Order | None
    session: FloorSession | None = None
