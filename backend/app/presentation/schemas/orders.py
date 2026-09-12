from __future__ import annotations

from typing import Literal

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
    # Modifier choices. Omitted/None = legacy client (plain line, no validation);
    # a list (even empty) = validated against the product's groups (422 if a
    # required group is unmet), deltas folded into the unit price.
    option_ids: list[str] | None = None
    # Override del curso por línea ("la provoleta como principal"); None = el
    # curso del producto en la carta.
    course: Literal["IMMEDIATE", "STARTER", "MAIN", "DESSERT"] | None = None


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


class SetItemCourseRequest(BaseModel):
    course: Literal["IMMEDIATE", "STARTER", "MAIN", "DESSERT"]


class SetItemNoteRequest(BaseModel):
    # None / empty clears the note.
    note: str | None = Field(default=None, max_length=280)


class TransferOrderRequest(BaseModel):
    table_id: str


class MergeOrdersRequest(BaseModel):
    # The order to absorb into this one (this order is the destination).
    source_order_id: str


class AssignWaiterRequest(BaseModel):
    # Reasignar el mozo dueño de la mesa (encargado). El user_id del nuevo mozo.
    waiter_id: str


class CreateOrderResponse(BaseModel):
    order_id: str


class SelectedOptionResponse(BaseModel):
    option_id: str
    name: str
    price_delta: int


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
    # Tiempo de servicio de la línea: IMMEDIATE | STARTER | MAIN | DESSERT.
    course: str = "MAIN"
    # ISO-8601; lets the KDS order items by how long they've been waiting.
    sent_at: str | None = None
    # Modificadores elegidos (Carta QR F2 D) — para el ticket de cocina / floor.
    selected_options: list[SelectedOptionResponse] = []


class OrderResponse(BaseModel):
    id: str
    table_id: str
    waiter_id: str
    status: str
    currency: str
    items: list[OrderItemResponse]
    total_amount: int
    # Cursos (derivados): el que está al fuego y el próximo en espera
    # ("Marchar principales"). None cuando no aplica.
    active_course: str | None = None
    next_course: str | None = None
    # Origen de la comanda (Carta QR F2): WAITER | CUSTOMER_QR. Default WAITER = paridad.
    source: str = "WAITER"
    # ISO-8601; lets the KDS show how long an order has been waiting.
    created_at: str | None = None
    # CRM: cliente atribuido a la comanda (None → sin atribuir).
    customer_id: str | None = None


class TaxQuoteResponse(BaseModel):
    """Sales tax to add on an order (minor units). For AR/IVA tax is 0 (included);
    for US it comes from the tax engine (TaxJar) by the tenant's fiscal address."""

    subtotal_amount: int
    tax_amount: int
    total_amount: int
    currency: str
    rate_bps: int
    jurisdiction: str | None = None
