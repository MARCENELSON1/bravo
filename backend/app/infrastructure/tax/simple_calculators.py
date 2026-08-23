"""Non-networked tax calculators: the tax-inclusive (AR) case and a flat rate.

``IncludedTaxCalculator`` answers "how much to add at checkout" for a
tax-inclusive regime (AR/IVA): nothing — it's already in the price.
``FlatRateTaxCalculator`` adds a fixed rate; it doubles as the deterministic
test double and as a v1 flat-rate fallback for a single-location US tenant that
hasn't wired an external engine.
"""

from __future__ import annotations

from app.domain.shared.money import Money
from app.domain.tax.ports import TaxCalculator
from app.domain.tax.value_objects import FiscalAddress, TaxCalculation


class IncludedTaxCalculator(TaxCalculator):
    async def calculate(self, *, taxable: Money, address: FiscalAddress) -> TaxCalculation:
        return TaxCalculation(
            subtotal=taxable,
            tax=Money.zero(taxable.currency),
            total=taxable,
            rate_bps=0,
        )


class FlatRateTaxCalculator(TaxCalculator):
    def __init__(self, rate_bps: int) -> None:
        self._rate_bps = rate_bps

    async def calculate(self, *, taxable: Money, address: FiscalAddress) -> TaxCalculation:
        tax = Money(round(taxable.amount * self._rate_bps / 10000), taxable.currency)
        return TaxCalculation(
            subtotal=taxable,
            tax=tax,
            total=taxable.plus(tax),
            rate_bps=self._rate_bps,
            jurisdiction=address.state or None,
        )
