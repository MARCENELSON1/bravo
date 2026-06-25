from __future__ import annotations

from pydantic import BaseModel

from app.presentation.schemas.orders import OrderResponse


class FloorTableResponse(BaseModel):
    id: str
    number: int
    name: str | None
    status: str  # "FREE" | "OCCUPIED"
    # The active order (with items + total + created_at) when occupied; the
    # frontend opens it instead of creating a duplicate.
    active_order: OrderResponse | None = None
