from __future__ import annotations

from pydantic import BaseModel, Field


class CreateOrderRequest(BaseModel):
    table_id: str
    # Optional client-generated id → idempotent create (a retry/replay is a no-op).
    id: str | None = None


class AddOrderItemRequest(BaseModel):
    product_id: str
    quantity: int = Field(ge=1)
    note: str | None = Field(default=None, max_length=255)
    # Optional client-generated id → idempotent add (a retry/replay is a no-op).
    id: str | None = None


class BatchOrderItem(BaseModel):
    product_id: str
    quantity: int = Field(ge=1)
    note: str | None = Field(default=None, max_length=255)
    id: str | None = None


class AddOrderItemsBatchRequest(BaseModel):
    """Add several items (and optionally send) in one round-trip."""

    items: list[BatchOrderItem] = Field(min_length=1)
    send: bool = False


class CreateOrderResponse(BaseModel):
    order_id: str


class OrderItemResponse(BaseModel):
    id: str
    product_id: str
    name: str
    unit_price_amount: int
    quantity: int
    note: str | None


class OrderResponse(BaseModel):
    id: str
    table_id: str
    waiter_id: str
    status: str
    currency: str
    items: list[OrderItemResponse]
    total_amount: int
