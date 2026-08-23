from __future__ import annotations

import json

import httpx

from app.domain.shared.money import Money
from app.domain.tax.value_objects import FiscalAddress
from app.domain.tenant.regional import TaxEngine
from app.infrastructure.tax.resolver import EngineTaxCalculatorResolver
from app.infrastructure.tax.simple_calculators import (
    FlatRateTaxCalculator,
    IncludedTaxCalculator,
)
from app.infrastructure.tax.taxjar_calculator import TaxJarCalculator

_ADDRESS = FiscalAddress(
    street="1218 3rd St", city="Santa Monica", state="CA", zip="90404", country="US"
)

# The exact shape TaxJar's sandbox returned for a $100 order in Santa Monica —
# this test locks our parsing against the real contract (validated live).
_TAXJAR_RESPONSE = {
    "tax": {
        "rate": 0.1075,
        "taxable_amount": 100.0,
        "amount_to_collect": 10.75,
        "has_nexus": True,
        "jurisdictions": {
            "state": "CA",
            "city": "SANTA MONICA",
            "county": "LOS ANGELES COUNTY",
            "country": "US",
        },
    }
}


async def test_included_calculator_adds_nothing():
    # Tax-inclusive (AR/IVA): nothing to add at checkout, total == subtotal.
    result = await IncludedTaxCalculator().calculate(taxable=Money(10000, "ARS"), address=_ADDRESS)
    assert result.tax == Money.zero("ARS")
    assert result.total == Money(10000, "ARS")
    assert result.rate_bps == 0


async def test_flat_rate_adds_on_top():
    result = await FlatRateTaxCalculator(rate_bps=1075).calculate(
        taxable=Money(10000, "USD"), address=_ADDRESS
    )
    assert result.tax == Money(1075, "USD")  # $10.75
    assert result.total == Money(11075, "USD")  # $110.75
    assert result.rate_bps == 1075


async def test_resolver_picks_by_engine():
    taxjar = FlatRateTaxCalculator(rate_bps=1075)  # stand-in
    included = IncludedTaxCalculator()
    resolver = EngineTaxCalculatorResolver(taxjar=taxjar, included=included)
    assert resolver.for_engine(TaxEngine.TAXJAR) is taxjar
    assert resolver.for_engine(TaxEngine.NONE) is included
    # AVALARA not built yet → degrades to the tax-inclusive calculator, no crash.
    assert resolver.for_engine(TaxEngine.AVALARA) is included


async def test_taxjar_calculator_parses_real_response():
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["body"] = json.loads(request.content)
        return httpx.Response(200, json=_TAXJAR_RESPONSE)

    calc = TaxJarCalculator("test-token", sandbox=True, transport=httpx.MockTransport(handler))
    result = await calc.calculate(taxable=Money(10000, "USD"), address=_ADDRESS)

    # Sent the taxable subtotal as major units to the calc endpoint.
    assert captured["url"].endswith("/v2/taxes")
    assert captured["body"]["amount"] == 100.0
    # Parsed the ADDED tax: $100 + $10.75 = $110.75 at 10.75%.
    assert result.tax == Money(1075, "USD")
    assert result.total == Money(11075, "USD")
    assert result.rate_bps == 1075
    assert result.jurisdiction == "SANTA MONICA, LOS ANGELES COUNTY, CA"
