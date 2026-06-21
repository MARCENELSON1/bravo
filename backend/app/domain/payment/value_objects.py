from __future__ import annotations

from enum import StrEnum


class PaymentDirection(StrEnum):
    """Whether the money comes in (cobro) or goes out (egreso/gasto)."""

    INFLOW = "INFLOW"
    OUTFLOW = "OUTFLOW"


class PaymentMethod(StrEnum):
    CASH = "CASH"
    CARD = "CARD"
    TRANSFER = "TRANSFER"
    MERCADOPAGO = "MERCADOPAGO"
    QR = "QR"


class PaymentStatus(StrEnum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"
