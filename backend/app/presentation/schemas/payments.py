from __future__ import annotations

from pydantic import BaseModel, Field

from app.domain.payment.value_objects import PaymentMethod


class RegisterPaymentRequest(BaseModel):
    method: PaymentMethod
    amount: int = Field(ge=1)  # minor units


class RegisterExpenseRequest(BaseModel):
    method: PaymentMethod
    amount: int = Field(ge=1)
    category: str | None = Field(default=None, max_length=60)
    counterparty: str | None = Field(default=None, max_length=120)
    description: str | None = Field(default=None, max_length=255)


class PaymentResponse(BaseModel):
    id: str
    direction: str
    order_id: str | None
    method: str
    amount: int
    currency: str
    status: str
    category: str | None
    counterparty: str | None
    description: str | None
    # Present only for online charges still awaiting confirmation: the payer is
    # redirected here (a Checkout Pro link, also usable as a QR).
    checkout_url: str | None = None
