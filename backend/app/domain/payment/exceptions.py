from __future__ import annotations

from app.domain.errors import DomainError


class PaymentNotFound(DomainError):
    code = "payment_not_found"
    message = "No encontramos el pago indicado."


class InvalidPaymentAmount(DomainError):
    code = "invalid_payment_amount"
    message = "El monto del pago debe ser mayor a cero."
