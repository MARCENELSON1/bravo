from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import UTC, datetime
from uuid import uuid4

from app.application.product.dtos import (
    CreateProductResult,
    PriceChange,
    PricingInsights,
    ProductPriceHistory,
    ProductPricingBase,
    ProductPricingRow,
    ProductRotation,
)
from app.domain.advisor.repository import AdvisorSettingsRepository
from app.domain.identity.ports import TenantContext
from app.domain.order.value_objects import Station
from app.domain.product.entities import Product
from app.domain.product.exceptions import ProductNotFound
from app.domain.product.repository import ProductRepository
from app.domain.shared.money import Money
from app.domain.tenant.exceptions import TenantNotFound
from app.domain.tenant.repository import TenantRepository

# A partir de cuánto se marca un precio como "rezagado" respecto de la inflación.
LAGGING_THRESHOLD_BPS = 500  # 5%


# --- Ports (read + write side de precios; impls en infrastructure) -----------


class PriceChangeRepository(ABC):
    """Append-only log de precios por producto. Scoped por ``tenant_id``."""

    @abstractmethod
    async def record(
        self,
        *,
        tenant_id: str,
        product_id: str,
        old_price_amount: int | None,
        new_price_amount: int,
        currency: str,
    ) -> None: ...

    @abstractmethod
    async def list_for_product(
        self, tenant_id: str, product_id: str
    ) -> list[PriceChange]: ...


class PricingReadModel(ABC):
    @abstractmethod
    async def base_rows(
        self, tenant_id: str
    ) -> tuple[str, list[ProductPricingBase]]:
        """Devuelve (moneda, filas): un producto activo por fila con su precio
        actual y la fecha de su último cambio (o su creación)."""
        ...


class RotationReadModel(ABC):
    @abstractmethod
    async def rotation(
        self,
        tenant_id: str,
        *,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> ProductRotation: ...


# --- Pure helper (testeable): "debería estar en $X" --------------------------


def suggested_price_amount(
    base_amount: int, monthly_inflation_bps: int, days_elapsed: int
) -> int:
    """Precio esperado si se ajustara por la inflación mensual estimada, compuesta
    sobre los meses (fraccionarios) transcurridos. Determinista; sin inflación,
    sin días o base no positiva → el mismo precio."""
    if monthly_inflation_bps <= 0 or days_elapsed <= 0 or base_amount <= 0:
        return base_amount
    monthly = monthly_inflation_bps / 10_000
    months = days_elapsed / 30
    return round(base_amount * (1 + monthly) ** months)


# --- Use cases ---------------------------------------------------------------


class CreateProduct:
    """Create a catalog product priced in the tenant's currency, and seed its
    price log with the initial price (baseline for "días desde el último cambio")."""

    def __init__(
        self,
        products: ProductRepository,
        tenants: TenantRepository,
        price_changes: PriceChangeRepository,
        tenant_context: TenantContext,
    ) -> None:
        self._products = products
        self._tenants = tenants
        self._price_changes = price_changes
        self._tenant_context = tenant_context

    async def execute(
        self,
        *,
        tenant_id: str,
        name: str,
        price_amount: int,
        category: str | None,
        station: Station = Station.KITCHEN,
        image_url: str | None = None,
        description: str | None = None,
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
            image_url=image_url,
            description=description,
        )
        await self._products.add(product)
        await self._price_changes.record(
            tenant_id=tenant_id,
            product_id=product.id,
            old_price_amount=None,
            new_price_amount=price_amount,
            currency=tenant.currency,
        )
        return CreateProductResult(product_id=product.id)


class ListProducts:
    def __init__(self, products: ProductRepository, tenant_context: TenantContext) -> None:
        self._products = products
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str, only_active: bool = False) -> list[Product]:
        self._tenant_context.set(tenant_id)
        return await self._products.list(tenant_id, only_active=only_active)


class SetProductAvailability:
    """The "86'd" toggle: mark a product available/unavailable for today. Distinct
    from deactivating it (a permanent delisting) — availability is a daily flag the
    QR menu reads to grey out (or hide) a dish that ran out."""

    def __init__(
        self,
        products: ProductRepository,
        tenant_context: TenantContext,
    ) -> None:
        self._products = products
        self._tenant_context = tenant_context

    async def execute(
        self, *, tenant_id: str, product_id: str, available_today: bool
    ) -> Product:
        self._tenant_context.set(tenant_id)
        product = await self._products.get_by_id(tenant_id, product_id)
        if product is None:
            raise ProductNotFound()
        product.set_availability(available_today)
        await self._products.save(product)
        return product


class UpdateProductPrice:
    """Reprice a product and record the change in its price log. A no-op price
    (same amount) is not logged."""

    def __init__(
        self,
        products: ProductRepository,
        price_changes: PriceChangeRepository,
        tenant_context: TenantContext,
    ) -> None:
        self._products = products
        self._price_changes = price_changes
        self._tenant_context = tenant_context

    async def execute(
        self, *, tenant_id: str, product_id: str, new_price_amount: int
    ) -> Product:
        self._tenant_context.set(tenant_id)
        product = await self._products.get_by_id(tenant_id, product_id)
        if product is None:
            raise ProductNotFound()
        old_amount = product.price.amount
        if new_price_amount == old_amount:
            return product
        product.change_price(new_price_amount)
        await self._products.save(product)
        await self._price_changes.record(
            tenant_id=tenant_id,
            product_id=product_id,
            old_price_amount=old_amount,
            new_price_amount=new_price_amount,
            currency=product.price.currency,
        )
        return product


class GetProductPriceHistory:
    """Histórico real de cambios de precio de un producto (para el simulador)."""

    def __init__(
        self,
        products: ProductRepository,
        price_changes: PriceChangeRepository,
        tenant_context: TenantContext,
    ) -> None:
        self._products = products
        self._price_changes = price_changes
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str, product_id: str) -> ProductPriceHistory:
        self._tenant_context.set(tenant_id)
        product = await self._products.get_by_id(tenant_id, product_id)
        if product is None:
            raise ProductNotFound()
        changes = await self._price_changes.list_for_product(tenant_id, product_id)
        return ProductPriceHistory(
            product_id=product_id,
            currency=product.price.currency,
            changes=changes,
        )


class GetPricingInsights:
    """Precios vs inflación: por cada producto, cuánto hace que no cambia el precio
    y a cuánto "debería estar" según la inflación mensual estimada del tenant."""

    def __init__(
        self,
        pricing: PricingReadModel,
        settings: AdvisorSettingsRepository,
        tenant_context: TenantContext,
    ) -> None:
        self._pricing = pricing
        self._settings = settings
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str, now: datetime | None = None) -> PricingInsights:
        self._tenant_context.set(tenant_id)
        reference = now or datetime.now(UTC)
        settings = await self._settings.get(tenant_id)
        inflation_bps = settings.monthly_inflation_bps if settings else 0
        currency, base_rows = await self._pricing.base_rows(tenant_id)
        if settings is not None:
            currency = settings.currency
        rows = [self._row(base, inflation_bps, reference) for base in base_rows]
        rows.sort(key=lambda r: r.gap_bps, reverse=True)
        return PricingInsights(
            currency=currency,
            monthly_inflation_bps=inflation_bps,
            configured=inflation_bps > 0,
            rows=rows,
        )

    @staticmethod
    def _row(
        base: ProductPricingBase, inflation_bps: int, reference: datetime
    ) -> ProductPricingRow:
        last = base.last_change_at
        if last.tzinfo is None:
            last = last.replace(tzinfo=UTC)
        days = max(0, (reference - last).days)
        current = base.current_price_amount
        suggested = suggested_price_amount(current, inflation_bps, days)
        gap = suggested - current
        gap_bps = round(gap / current * 10_000) if current > 0 else 0
        return ProductPricingRow(
            product_id=base.product_id,
            product_name=base.product_name,
            current_price_amount=current,
            suggested_price_amount=suggested,
            gap_amount=gap,
            gap_bps=gap_bps,
            days_since_change=days,
            lagging=gap_bps >= LAGGING_THRESHOLD_BPS,
        )


class GetProductRotation:
    """Rotación por día de semana (Lun–Dom) a partir de sale_facts."""

    def __init__(
        self, rotation: RotationReadModel, tenant_context: TenantContext
    ) -> None:
        self._rotation = rotation
        self._tenant_context = tenant_context

    async def execute(
        self,
        *,
        tenant_id: str,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> ProductRotation:
        self._tenant_context.set(tenant_id)
        return await self._rotation.rotation(tenant_id, since=since, until=until)
