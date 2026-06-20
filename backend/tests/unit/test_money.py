from __future__ import annotations

import pytest

from app.domain.shared.exceptions import (
    CurrencyMismatch,
    InvalidMoneyAmount,
    UnsupportedCurrency,
)
from app.domain.shared.money import Money


def test_money_normalizes_currency() -> None:
    m = Money(1500, "ars")
    assert m.amount == 1500
    assert m.currency == "ARS"


def test_money_times_and_plus() -> None:
    assert Money(1500, "ARS").times(3).amount == 4500
    assert Money(1500, "ARS").plus(Money(800, "ARS")).amount == 2300


def test_money_zero() -> None:
    assert Money.zero("ARS").amount == 0


def test_money_currency_mismatch_on_plus() -> None:
    with pytest.raises(CurrencyMismatch):
        Money(1500, "ARS").plus(Money(100, "USD"))


def test_money_rejects_negative() -> None:
    with pytest.raises(InvalidMoneyAmount):
        Money(-1, "ARS")


def test_money_rejects_unsupported_currency() -> None:
    with pytest.raises(UnsupportedCurrency):
        Money(100, "XXX")
