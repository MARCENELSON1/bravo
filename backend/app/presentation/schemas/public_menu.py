from __future__ import annotations

from datetime import datetime

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
    # ``requires_confirmation`` refleja el gate Salón: true → el mozo confirma.
    requires_confirmation: bool
    # ``prepay_required`` (Fase 3, Autoservicio): true → la orden está retenida y el
    # comensal debe pagar (con /public/table/pay) para que llegue a la cocina.
    prepay_required: bool = False


class TableBillOptionResponse(BaseModel):
    name: str
    price_delta: int


class TableBillItemResponse(BaseModel):
    name: str
    quantity: int
    unit_price: int
    selected_options: list[TableBillOptionResponse] = Field(default_factory=list)


class TableBillResponse(BaseModel):
    """La cuenta de la mesa que ve el comensal (Carta QR F3). Todo server-side:
    total/pagado/saldo en minor units. ``online_pay_available`` decide si la carta
    ofrece pagar online o cae a "pagá con el mozo"; ``tips_enabled`` muestra/oculta
    el selector de propina."""

    currency: str
    items: list[TableBillItemResponse]
    total: int
    paid: int
    balance: int
    online_pay_available: bool
    tips_enabled: bool


class TablePayRequest(BaseModel):
    """El comensal inicia el pago (Carta QR F3). El monto lo acota el server (saldo
    de la orden). ``amount`` opcional = dividir la cuenta / pagar una parte (0 <
    amount ≤ saldo); ausente = pagar todo el saldo. La ``idempotency_key`` evita
    que un doble-tap cobre dos veces."""

    token: str
    tip: int = Field(default=0, ge=0)
    amount: int | None = Field(default=None, gt=0)
    idempotency_key: str | None = Field(default=None, max_length=80)


class TablePayResponse(BaseModel):
    payment_id: str
    order_id: str
    # PENDING (esperando la pasarela) / CONFIRMED (ya pagó, p.ej. gateway manual).
    status: str
    amount: int
    tip: int
    # A dónde mandar al comensal a pagar online; null si el cobro ya se confirmó.
    checkout_url: str | None = None


class PublicPaymentStatusResponse(BaseModel):
    payment_id: str
    status: str
    amount: int
    tip: int


class PublicReceiptItemResponse(BaseModel):
    name: str
    quantity: int
    unit_price: int
    selected_options: list[TableBillOptionResponse] = Field(default_factory=list)


class PublicPaymentReceiptResponse(BaseModel):
    """Recibo NO fiscal del comensal tras pagar (Carta QR F3). No es factura AFIP."""

    venue_name: str
    currency: str
    items: list[PublicReceiptItemResponse]
    amount: int
    tip: int
    method: str
    paid_at: datetime | None = None
