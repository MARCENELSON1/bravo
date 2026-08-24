from __future__ import annotations

from pydantic import BaseModel, Field

from app.domain.payment.value_objects import PaymentMethod


class RegisterPaymentRequest(BaseModel):
    method: PaymentMethod
    amount: int = Field(ge=1)  # minor units
    tip: int = Field(default=0, ge=0)  # propina encima de amount (minor units)
    tax: int = Field(default=0, ge=0)  # sales tax incluido en amount (minor units)


class RegisterExpenseRequest(BaseModel):
    method: PaymentMethod
    amount: int = Field(ge=1)
    category: str | None = Field(default=None, max_length=60)
    counterparty: str | None = Field(default=None, max_length=120)
    description: str | None = Field(default=None, max_length=255)


class FeeRateItem(BaseModel):
    """Comisiones (slice B): la tasa de un método, en bps (300 = 3%)."""

    method: PaymentMethod
    fee_bps: int = Field(ge=0, le=10000)


class UpdateFeeRatesRequest(BaseModel):
    rates: list[FeeRateItem]


class FeeRatesResponse(BaseModel):
    rates: list[FeeRateItem]


class PaymentResponse(BaseModel):
    id: str
    direction: str
    order_id: str | None
    method: str
    amount: int
    tip_amount: int
    tax_amount: int
    currency: str
    status: str
    category: str | None
    counterparty: str | None
    description: str | None
    # Present only for online charges still awaiting confirmation: the payer is
    # redirected here (a Checkout Pro link, also usable as a QR).
    checkout_url: str | None = None
