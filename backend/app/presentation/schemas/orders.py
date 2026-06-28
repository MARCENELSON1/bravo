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


class SetItemQuantityRequest(BaseModel):
    quantity: int = Field(ge=1)


class TransferOrderRequest(BaseModel):
    table_id: str


class MergeOrdersRequest(BaseModel):
    # The order to absorb into this one (this order is the destination).
    source_order_id: str


class CreateOrderResponse(BaseModel):
    order_id: str


class OrderItemResponse(BaseModel):
    id: str
    product_id: str
    name: str
    unit_price_amount: int
    quantity: int
    note: str | None
    # Per-item kitchen lifecycle (Fase 14) — drives the per-station KDS board.
    status: str
    station: str
    # ISO-8601; lets the KDS order items by how long they've been waiting.
    sent_at: str | None = None


class OrderResponse(BaseModel):
    id: str
    table_id: str
    waiter_id: str
    status: str
    currency: str
    items: list[OrderItemResponse]
    total_amount: int
    # ISO-8601; lets the KDS show how long an order has been waiting.
    created_at: str | None = None
