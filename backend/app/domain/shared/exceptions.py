from __future__ import annotations

from app.domain.errors import DomainError


class UnsupportedCurrency(DomainError):
    code = "unsupported_currency"
    message = "La moneda no está soportada."


class InvalidMoneyAmount(DomainError):
    code = "invalid_money_amount"
    message = "El monto no es válido."


class CurrencyMismatch(DomainError):
    code = "currency_mismatch"
    message = "No se pueden operar montos en monedas distintas."
