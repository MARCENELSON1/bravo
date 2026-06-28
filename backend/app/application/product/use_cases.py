from __future__ import annotations

from uuid import uuid4

from app.application.product.dtos import CreateProductResult
from app.domain.identity.ports import TenantContext
from app.domain.order.value_objects import Station
from app.domain.product.entities import Product
from app.domain.product.repository import ProductRepository
from app.domain.shared.money import Money
from app.domain.tenant.exceptions import TenantNotFound
from app.domain.tenant.repository import TenantRepository


class CreateProduct:
    """Create a catalog product priced in the tenant's currency."""

    def __init__(
        self,
        products: ProductRepository,
        tenants: TenantRepository,
        tenant_context: TenantContext,
    ) -> None:
        self._products = products
        self._tenants = tenants
        self._tenant_context = tenant_context

    async def execute(
        self,
        *,
        tenant_id: str,
        name: str,
        price_amount: int,
        category: str | None,
        station: Station = Station.KITCHEN,
    ) -> CreateProductResult:
        self._tenant_context.set(tenant_id)
        tenant = await self._tenants.get_by_id(tenant_id)
        if tenant is None:
            raise TenantNotFound()
        product = Product(
            id=str(uuid4()),
            tenant_id=tenant_id,
            name=name,
            price=Money(price_amount, tenant.currency),
            category=category,
            station=station,
        )
        await self._products.add(product)
        return CreateProductResult(product_id=product.id)


class ListProducts:
    def __init__(self, products: ProductRepository, tenant_context: TenantContext) -> None:
        self._products = products
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str, only_active: bool = False) -> list[Product]:
        self._tenant_context.set(tenant_id)
        return await self._products.list(tenant_id, only_active=only_active)
