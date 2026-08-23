"""The one place the AR-vs-US tax decision is made: a lookup by ``tax_engine``.

Both calculators satisfy the same ``TaxCalculator`` port, so consumers stay
engine-agnostic — they ask the resolver for "the calculator of this tenant's
engine" and call ``.calculate(...)``. AVALARA isn't built yet → it degrades to
the tax-inclusive calculator (no crash) until its adapter lands.
"""

from __future__ import annotations

from app.domain.tax.ports import TaxCalculator
from app.domain.tenant.regional import TaxEngine


class EngineTaxCalculatorResolver:
    def __init__(self, *, taxjar: TaxCalculator, included: TaxCalculator) -> None:
        self._by_engine: dict[TaxEngine, TaxCalculator] = {
            TaxEngine.TAXJAR: taxjar,
            TaxEngine.NONE: included,
            TaxEngine.AVALARA: included,  # not built yet → degrade, don't crash
        }

    def for_engine(self, engine: TaxEngine) -> TaxCalculator:
        return self._by_engine.get(engine, self._by_engine[TaxEngine.NONE])
