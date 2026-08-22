from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.presentation.schemas.orders import OrderResponse


class FloorSessionResponse(BaseModel):
    """The session-aware live view of a table (derived state + timer + pax)."""

    id: str
    # "OPEN" | "IN_KITCHEN" | "TO_SERVE" | "SERVED" | "TO_CHARGE" | "CLOSED"
    state: str
    state_since: datetime | None = None  # ISO-8601; the floor timer runs from here
    pax: int | None = None
    waiter_id: str | None = None
    waiter_name: str | None = None
    sector_id: str | None = None


class FloorTableResponse(BaseModel):
    id: str
    number: int
    name: str | None
    status: str  # "FREE" | "OCCUPIED"
    # The active order (with items + total + created_at) when occupied; the
    # frontend opens it instead of creating a duplicate.
    active_order: OrderResponse | None = None
    # Additive session view (state/timer/pax); None → table free or no session.
    session: FloorSessionResponse | None = None
    # The table's sector (for grouping free tables too) + capacity. None → unassigned.
    sector_id: str | None = None
    capacity: int | None = None


class OpenSessionRequest(BaseModel):
    table_id: str
    pax: int | None = Field(default=None, ge=1)
    waiter_id: str | None = None


class SetSessionPaxRequest(BaseModel):
    pax: int = Field(ge=1)


class SessionResponse(BaseModel):
    id: str
    table_id: str
    status: str
    pax: int | None = None
    waiter_id: str | None = None
