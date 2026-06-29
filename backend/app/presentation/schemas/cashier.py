from __future__ import annotations

from pydantic import BaseModel, Field

from app.domain.payment.value_objects import PaymentMethod


class OpenCashSessionRequest(BaseModel):
    opening_float_amount: int = Field(ge=0)  # minor units (cash in the drawer)
    note: str | None = Field(default=None, max_length=255)


class CloseCashSessionRequest(BaseModel):
    # Counted amount (minor units) per payment method.
    counted: dict[PaymentMethod, int]
    note: str | None = Field(default=None, max_length=255)


class CashSessionResponse(BaseModel):
    id: str
    status: str
    currency: str
    opening_float_amount: int
    opened_at: str | None = None


class CashReportLineResponse(BaseModel):
    method: str
    expected: int
    tips: int
    counted: int | None
    difference: int | None


class CashReportResponse(BaseModel):
    session_id: str
    status: str
    currency: str
    opening_float: int
    opened_at: str | None
    closed_at: str | None
    lines: list[CashReportLineResponse]
    expected_total: int
    counted_total: int | None
    difference_total: int | None
    tips_total: int
