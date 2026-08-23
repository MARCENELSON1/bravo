from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.shared.money import Money
from app.domain.tax.value_objects import FiscalAddress, TaxCalculation


class TaxCalculator(ABC):
    """Computes the sales tax to add on top of a taxable subtotal for a given
    point-of-sale address.

    Adapters: ``TaxJarCalculator`` (real rate by jurisdiction), ``FlatRateTaxCalculator``
    (deterministic, for tests / a v1 flat rate) and ``IncludedTaxCalculator``
    (tax-inclusive regime → nothing to add). Which one runs is chosen per tenant
    by the engine resolver from ``tenant.tax_engine``.
    """

    @abstractmethod
    async def calculate(self, *, taxable: Money, address: FiscalAddress) -> TaxCalculation: ...
