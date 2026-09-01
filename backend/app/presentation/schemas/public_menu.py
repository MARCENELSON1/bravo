from __future__ import annotations

from pydantic import BaseModel, Field


class PublicMenuModifierOptionResponse(BaseModel):
    id: str
    name: str
    price_delta: int


class PublicMenuModifierGroupResponse(BaseModel):
    id: str
    name: str
    min_select: int
    max_select: int
    required: bool
    options: list[PublicMenuModifierOptionResponse]


class PublicMenuItemResponse(BaseModel):
    id: str
    name: str
    price_amount: int
    image_url: str | None = None
    description: str | None = None
    available_today: bool = True
    modifier_groups: list[PublicMenuModifierGroupResponse] = Field(default_factory=list)


class PublicMenuCategoryResponse(BaseModel):
    name: str | None
    items: list[PublicMenuItemResponse]


class PublicMenuResponse(BaseModel):
    tenant_name: str
    currency: str
    locale: str
    categories: list[PublicMenuCategoryResponse]
    # Gate del autopedido: si está apagado, la carta no muestra carrito.
    self_order_enabled: bool = False
    self_order_requires_confirmation: bool = True


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
    # Ids de las opciones de modificador elegidas (el server resuelve precio + min/max).
    option_ids: list[str] = Field(default_factory=list)


class CustomerOrderRequest(BaseModel):
    token: str
    lines: list[CustomerOrderLine] = Field(min_length=1)


class CustomerOrderResponse(BaseModel):
    order_id: str
    status: str
    # ``requires_confirmation`` refleja el gate: true → el mozo tiene que confirmar.
    requires_confirmation: bool
