from __future__ import annotations

from pydantic import BaseModel, Field

from app.domain.cashier.value_objects import CashMovementKind
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


class CashMovementRowResponse(BaseModel):
    id: str
    kind: str  # "DEPOSIT" | "DROP" | "PAYOUT"
    amount: int
    signed_amount: int  # efecto en el cajón (+ingreso / −salida)
    reason: str | None
    created_at: str | None


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
    movements: list[CashMovementRowResponse] = []
    cash_in_total: int = 0
    cash_out_total: int = 0
    blind: bool = False  # arqueo ciego: el esperado va enmascarado mientras OPEN


class CashSettingsRequest(BaseModel):
    require_open_cash_session: bool = False
    blind_cash_count: bool = False


class CashSettingsResponse(BaseModel):
    require_open_cash_session: bool
    blind_cash_count: bool


class CashMovementRequest(BaseModel):
    kind: CashMovementKind
    amount: int = Field(ge=1)  # minor units (siempre positivo; el kind da el signo)
    reason: str | None = Field(default=None, max_length=255)


class CashMovementResponse(BaseModel):
    id: str
    kind: str
    amount: int
    signed_amount: int
    currency: str
    reason: str | None


class TipsReportRowResponse(BaseModel):
    waiter_id: str
    waiter_name: str  # nombre del mozo (fallback email); nunca el UUID
    earned: int  # propina ganada (minor units)
    paid: int  # ya liquidado al mozo
    pending: int  # earned - paid


class TipsReportResponse(BaseModel):
    currency: str
    rows: list[TipsReportRowResponse]
    earned_total: int
    paid_total: int
    pending_total: int


class TipPayoutRequest(BaseModel):
    waiter_id: str
    amount: int = Field(ge=1)  # minor units
    method: PaymentMethod = PaymentMethod.CASH


class TipPayoutResponse(BaseModel):
    """Guarda D: liquidación en el ledger de propinas (no es un egreso)."""

    id: str
    waiter_id: str
    amount: int
    currency: str
    method: str
