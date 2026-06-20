from __future__ import annotations

from dataclasses import dataclass

from app.domain.shared.exceptions import (
    CurrencyMismatch,
    InvalidMoneyAmount,
    UnsupportedCurrency,
)

# ISO 4217 codes supported at launch (Argentina/ARS first; the rest enable
# multi-country later). Amounts are integers in the currency's minor unit.
_SUPPORTED_CURRENCIES = frozenset({"ARS", "USD", "EUR", "BRL", "UYU", "CLP", "PYG"})


@dataclass(frozen=True)
class Money:
    """A monetary amount: an integer in the minor unit + an ISO-4217 currency.

    Never use floats for money. ``amount`` is e.g. centavos for ARS.
    """

    amount: int
    currency: str

    def __post_init__(self) -> None:
        currency = self.currency.upper()
        if currency not in _SUPPORTED_CURRENCIES:
            raise UnsupportedCurrency()
        if self.amount < 0:
            raise InvalidMoneyAmount()
        object.__setattr__(self, "currency", currency)

    @staticmethod
    def zero(currency: str) -> Money:
        return Money(0, currency)

    def times(self, quantity: int) -> Money:
        if quantity < 0:
            raise InvalidMoneyAmount()
        return Money(self.amount * quantity, self.currency)

    def plus(self, other: Money) -> Money:
        if other.currency != self.currency:
            raise CurrencyMismatch()
        return Money(self.amount + other.amount, self.currency)

    def __str__(self) -> str:
        return f"{self.currency} {self.amount}"
