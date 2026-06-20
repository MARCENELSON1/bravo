from __future__ import annotations

from pydantic import BaseModel, Field


class CreateOrderRequest(BaseModel):
    table_id: str


class AddOrderItemRequest(BaseModel):
    product_id: str
    quantity: int = Field(ge=1)
    note: str | None = Field(default=None, max_length=255)


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
