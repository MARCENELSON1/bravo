from __future__ import annotations

import pytest

from app.application.tax.quote_order_tax import QuoteOrderTax
from app.domain.order.exceptions import OrderNotFound
from app.domain.shared.money import Money
from app.domain.tenant.entities import Tenant
from app.domain.tenant.regional import TaxEngine, TaxRegime
from app.infrastructure.tax.resolver import EngineTaxCalculatorResolver
from app.infrastructure.tax.simple_calculators import (
    FlatRateTaxCalculator,
    IncludedTaxCalculator,
)


class _StubOrder:
    def __init__(self, order_id: str, total: Money) -> None:
        self.id = order_id
        self._total = total

    def total(self) -> Money:
        return self._total


class _FakeOrders:
    def __init__(self, order: _StubOrder | None) -> None:
        self._order = order

    async def get_by_id(self, tenant_id: str, order_id: str) -> _StubOrder | None:
        if self._order is not None and self._order.id == order_id:
            return self._order
        return None


class _FakeTenants:
    def __init__(self, tenant: Tenant | None) -> None:
        self._tenant = tenant

    async def get_by_id(self, tenant_id: str) -> Tenant | None:
        return self._tenant


class _NoopCtx:
    def set(self, tenant_id: str) -> None:
        pass


def _resolver() -> EngineTaxCalculatorResolver:
    return EngineTaxCalculatorResolver(
        taxjar=FlatRateTaxCalculator(rate_bps=1075), included=IncludedTaxCalculator()
    )


def _tenant(**kw) -> Tenant:
    return Tenant(id="t1", slug="s", name="n", **kw)


async def test_us_tenant_gets_added_tax():
    order = _StubOrder("o1", Money(10000, "USD"))
    tenant = _tenant(
        country="US",
        currency="USD",
        tax_engine=TaxEngine.TAXJAR,
        tax_regime=TaxRegime.US_SALES_TAX,
        fiscal_state="CA",
        fiscal_zip="90404",
    )
    uc = QuoteOrderTax(_FakeOrders(order), _FakeTenants(tenant), _resolver(), _NoopCtx())
    quote = await uc.execute(tenant_id="t1", order_id="o1")
    assert quote.subtotal == Money(10000, "USD")
    assert quote.tax == Money(1075, "USD")
    assert quote.total == Money(11075, "USD")
    assert quote.rate_bps == 1075


async def test_ar_tenant_adds_nothing():
    # Defaults: AR, tax_engine NONE → tax-inclusive, nothing to add (parity).
    order = _StubOrder("o1", Money(10000, "ARS"))
    uc = QuoteOrderTax(_FakeOrders(order), _FakeTenants(_tenant()), _resolver(), _NoopCtx())
    quote = await uc.execute(tenant_id="t1", order_id="o1")
    assert quote.tax == Money.zero("ARS")
    assert quote.total == Money(10000, "ARS")
    assert quote.rate_bps == 0


async def test_missing_order_raises():
    uc = QuoteOrderTax(_FakeOrders(None), _FakeTenants(_tenant()), _resolver(), _NoopCtx())
    with pytest.raises(OrderNotFound):
        await uc.execute(tenant_id="t1", order_id="missing")
