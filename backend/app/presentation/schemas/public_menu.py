from __future__ import annotations

from pydantic import BaseModel, Field


class PublicMenuItemResponse(BaseModel):
    id: str
    name: str
    price_amount: int
    image_url: str | None = None
    description: str | None = None
    available_today: bool = True


class PublicMenuCategoryResponse(BaseModel):
    name: str | None
    items: list[PublicMenuItemResponse]


class PublicMenuResponse(BaseModel):
    tenant_name: str
    currency: str
    locale: str
    categories: list[PublicMenuCategoryResponse]


class IssueTableQrResponse(BaseModel):
    token: str
    url: str


class TableCallRequest(BaseModel):
    token: str


class TableCallResponse(BaseModel):
    status: str = "ok"


class CustomerOrderLine(BaseModel):
    product_id: str
    quantity: int = Field(ge=1)
    note: str | None = Field(default=None, max_length=280)


class CustomerOrderRequest(BaseModel):
    token: str
    lines: list[CustomerOrderLine] = Field(min_length=1)


class CustomerOrderResponse(BaseModel):
    order_id: str
    status: str
    # ``requires_confirmation`` refleja el gate: true → el mozo tiene que confirmar.
    requires_confirmation: bool
