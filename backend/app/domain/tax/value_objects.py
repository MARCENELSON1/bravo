from __future__ import annotations

from dataclasses import dataclass

from app.domain.shared.money import Money


@dataclass(frozen=True)
class FiscalAddress:
    """A point-of-sale address for tax purposes (the restaurant's location).

    For a dine-in restaurant the sale is sourced at the venue, so ``from`` and
    ``to`` are the same address when we ask the tax engine.
    """

    street: str
    city: str
    state: str
    zip: str
    country: str = "US"


@dataclass(frozen=True)
class TaxCalculation:
    """How much sales tax to ADD on top of a taxable subtotal, and the total.

    Integer minor units throughout (like Money). For a tax-inclusive regime
    (AR/IVA) there is nothing to add at checkout → ``tax`` is zero and
    ``total == subtotal``. ``rate_bps`` is the combined rate in basis points
    (1075 = 10.75%), for display.
    """

    subtotal: Money
    tax: Money
    total: Money
    rate_bps: int
    jurisdiction: str | None = None
