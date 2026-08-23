from __future__ import annotations

from app.domain.identity.ports import TenantContext
from app.domain.order.exceptions import OrderNotFound
from app.domain.order.repository import OrderRepository
from app.domain.tax.ports import TaxEngineResolver
from app.domain.tax.value_objects import FiscalAddress, TaxCalculation
from app.domain.tenant.repository import TenantRepository


def _fiscal_address(tenant) -> FiscalAddress:  # noqa: ANN001 (domain Tenant)
    return FiscalAddress(
        street=tenant.fiscal_street or "",
        city=tenant.fiscal_city or "",
        state=tenant.fiscal_state or "",
        zip=tenant.fiscal_zip or "",
        country=tenant.country or "US",
    )


class QuoteOrderTax:
    """Read-only: how much sales tax to add on an order for this tenant.

    Picks the calculator from ``tenant.tax_engine`` (the resolver): AR (NONE) →
    tax-inclusive, nothing to add; US (TAXJAR) → TaxJar's rate by the tenant's
    fiscal address. Never mutates the order or issues anything.
    """

    def __init__(
        self,
        orders: OrderRepository,
        tenants: TenantRepository,
        resolver: TaxEngineResolver,
        tenant_context: TenantContext,
    ) -> None:
        self._orders = orders
        self._tenants = tenants
        self._resolver = resolver
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str, order_id: str) -> TaxCalculation:
        self._tenant_context.set(tenant_id)
        order = await self._orders.get_by_id(tenant_id, order_id)
        if order is None:
            raise OrderNotFound()
        tenant = await self._tenants.get_by_id(tenant_id)
        if tenant is None:
            raise OrderNotFound()
        calculator = self._resolver.for_engine(tenant.tax_engine)
        return await calculator.calculate(
            taxable=order.total(), address=_fiscal_address(tenant)
        )
