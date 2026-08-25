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


@dataclass(frozen=True)
class TaxSale:
    """A settled taxable sale, reported to the tax provider so it can be filed
    and remitted (TaxJar AutoFile).

    ``amount`` is the taxable subtotal EXCLUDING the collected ``sales_tax`` (the
    provider adds them back itself). ``transaction_id`` is the order id, so
    re-reporting the same sale is idempotent on the provider's side.
    ``occurred_at`` is an ISO-8601 timestamp (when the order was settled).
    """

    transaction_id: str
    amount: Money
    sales_tax: Money
    address: FiscalAddress
    occurred_at: str
