from __future__ import annotations

from app.domain.inventory.entities import Ingredient
from app.domain.inventory.recipe import Preparation
from app.domain.inventory.repository import IngredientRepository, PreparationRepository
from app.domain.product.entities import Product
from app.domain.product.modifier_repository import ModifierRepository
from app.domain.product.modifiers import ModifierGroup
from app.domain.product.repository import ProductRepository
from app.domain.shared.cache import CATALOG_TTL_SECONDS, CachePort, namespace_for
from app.domain.table.entities import Table
from app.domain.table.repository import TableRepository
from app.domain.table_session.entities import Sector
from app.domain.table_session.repository import SectorRepository

# Catalog decorators. Each one wraps the real repository and implements the same
# port, so the domain and the use cases never learn that a cache exists — the
# swap happens in `container.py` and can be undone by wiring the plain repo back.
#
# Only *catalog* data is cached: read on nearly every request, written by an
# owner once in a while. Live state (orders, payments, table sessions, stock
# movements) is deliberately never cached — a stale order is a broken service.
#
# Every write bumps the namespace version, so an edited price is visible on the
# very next read (see `CachePort` for why versioning instead of delete-by-pattern).


class _CachedRepository:
    """Shared key building + invalidation for the catalog decorators."""

    _entity: str

    def __init__(self, cache: CachePort, ttl_seconds: int = CATALOG_TTL_SECONDS) -> None:
        self._cache = cache
        self._ttl = ttl_seconds

    def _namespace(self, tenant_id: str) -> str:
        return namespace_for(self._entity, tenant_id)

    async def _key(self, tenant_id: str, suffix: str) -> str:
        version = await self._cache.namespace_version(self._namespace(tenant_id))
        return f"{self._namespace(tenant_id)}:v{version}:{suffix}"

    async def _invalidate(self, tenant_id: str) -> None:
        await self._cache.bump_namespace(self._namespace(tenant_id))


class CachedProductRepository(_CachedRepository, ProductRepository):
    """Products: read on every order, payment projection and QR menu load."""

    _entity = "products"

    def __init__(
        self,
        inner: ProductRepository,
        cache: CachePort,
        ttl_seconds: int = CATALOG_TTL_SECONDS,
    ) -> None:
        super().__init__(cache, ttl_seconds)
        self._inner = inner

    async def get_by_id(self, tenant_id: str, product_id: str) -> Product | None:
        key = await self._key(tenant_id, f"id:{product_id}")
        cached = await self._cache.get(key)
        if cached is not None:
            return cached
        product = await self._inner.get_by_id(tenant_id, product_id)
        if product is not None:
            await self._cache.set(key, product, self._ttl)
        return product

    async def list(self, tenant_id: str, *, only_active: bool = False) -> list[Product]:
        key = await self._key(tenant_id, f"list:active={only_active}")
        cached = await self._cache.get(key)
        if cached is not None:
            return list(cached)  # copy: callers must not mutate the cached list
        products = await self._inner.list(tenant_id, only_active=only_active)
        await self._cache.set(key, list(products), self._ttl)
        return products

    async def list_for_ids(self, tenant_id: str, product_ids: list[str]) -> list[Product]:
        if not product_ids:
            return []
        key = await self._key(tenant_id, f"ids:{','.join(sorted(set(product_ids)))}")
        cached = await self._cache.get(key)
        if cached is not None:
            return list(cached)
        products = await self._inner.list_for_ids(tenant_id, product_ids)
        await self._cache.set(key, list(products), self._ttl)
        return products

    async def add(self, product: Product) -> None:
        await self._inner.add(product)
        await self._invalidate(product.tenant_id)

    async def save(self, product: Product) -> None:
        await self._inner.save(product)
        await self._invalidate(product.tenant_id)


class CachedIngredientRepository(_CachedRepository, IngredientRepository):
    """Ingredients: read on every paid order to price the recipes."""

    _entity = "ingredients"

    def __init__(
        self,
        inner: IngredientRepository,
        cache: CachePort,
        ttl_seconds: int = CATALOG_TTL_SECONDS,
    ) -> None:
        super().__init__(cache, ttl_seconds)
        self._inner = inner

    async def get_by_id(self, tenant_id: str, ingredient_id: str) -> Ingredient | None:
        return await self._inner.get_by_id(tenant_id, ingredient_id)

    async def list_below_min(self, tenant_id: str) -> list[Ingredient]:
        # Depends on live stock levels, not just the catalog → never cached.
        return await self._inner.list_below_min(tenant_id)

    async def list(self, tenant_id: str, *, active_only: bool = False) -> list[Ingredient]:
        key = await self._key(tenant_id, f"list:active={active_only}")
        cached = await self._cache.get(key)
        if cached is not None:
            return list(cached)
        ingredients = await self._inner.list(tenant_id, active_only=active_only)
        await self._cache.set(key, list(ingredients), self._ttl)
        return ingredients

    async def add(self, ingredient: Ingredient) -> None:
        await self._inner.add(ingredient)
        await self._invalidate(ingredient.tenant_id)

    async def save(self, ingredient: Ingredient) -> None:
        await self._inner.save(ingredient)
        await self._invalidate(ingredient.tenant_id)


class CachedPreparationRepository(_CachedRepository, PreparationRepository):
    """Preparations (recetas madre): read on every paid order with a recipe."""

    _entity = "preparations"

    def __init__(
        self,
        inner: PreparationRepository,
        cache: CachePort,
        ttl_seconds: int = CATALOG_TTL_SECONDS,
    ) -> None:
        super().__init__(cache, ttl_seconds)
        self._inner = inner

    async def get(self, tenant_id: str, preparation_id: str) -> Preparation | None:
        return await self._inner.get(tenant_id, preparation_id)

    async def list(self, tenant_id: str) -> list[Preparation]:
        key = await self._key(tenant_id, "list")
        cached = await self._cache.get(key)
        if cached is not None:
            return list(cached)
        preparations = await self._inner.list(tenant_id)
        await self._cache.set(key, list(preparations), self._ttl)
        return preparations

    async def usage_counts(self, tenant_id: str) -> dict[str, int]:
        return await self._inner.usage_counts(tenant_id)

    async def save(self, preparation: Preparation) -> None:
        await self._inner.save(preparation)
        await self._invalidate(preparation.tenant_id)

    async def delete(self, tenant_id: str, preparation_id: str) -> None:
        await self._inner.delete(tenant_id, preparation_id)
        await self._invalidate(tenant_id)


class CachedTableRepository(_CachedRepository, TableRepository):
    """Tables: read on every `GET /floor`, which each device polls on a timer."""

    _entity = "tables"

    def __init__(
        self,
        inner: TableRepository,
        cache: CachePort,
        ttl_seconds: int = CATALOG_TTL_SECONDS,
    ) -> None:
        super().__init__(cache, ttl_seconds)
        self._inner = inner

    async def get_by_id(self, tenant_id: str, table_id: str) -> Table | None:
        key = await self._key(tenant_id, f"id:{table_id}")
        cached = await self._cache.get(key)
        if cached is not None:
            return cached
        table = await self._inner.get_by_id(tenant_id, table_id)
        if table is not None:
            await self._cache.set(key, table, self._ttl)
        return table

    async def list(self, tenant_id: str) -> list[Table]:
        key = await self._key(tenant_id, "list")
        cached = await self._cache.get(key)
        if cached is not None:
            return list(cached)
        tables = await self._inner.list(tenant_id)
        await self._cache.set(key, list(tables), self._ttl)
        return tables

    async def add(self, table: Table) -> None:
        await self._inner.add(table)
        await self._invalidate(table.tenant_id)

    async def save(self, table: Table) -> None:
        await self._inner.save(table)
        await self._invalidate(table.tenant_id)


class CachedSectorRepository(_CachedRepository, SectorRepository):
    """Sectors (salon zones): read alongside the tables on every floor render."""

    _entity = "sectors"

    def __init__(
        self,
        inner: SectorRepository,
        cache: CachePort,
        ttl_seconds: int = CATALOG_TTL_SECONDS,
    ) -> None:
        super().__init__(cache, ttl_seconds)
        self._inner = inner

    async def get_by_id(self, tenant_id: str, sector_id: str) -> Sector | None:
        return await self._inner.get_by_id(tenant_id, sector_id)

    async def list(self, tenant_id: str) -> list[Sector]:
        key = await self._key(tenant_id, "list")
        cached = await self._cache.get(key)
        if cached is not None:
            return list(cached)
        sectors = await self._inner.list(tenant_id)
        await self._cache.set(key, list(sectors), self._ttl)
        return sectors

    async def add(self, sector: Sector) -> None:
        await self._inner.add(sector)
        await self._invalidate(sector.tenant_id)

    async def save(self, sector: Sector) -> None:
        await self._inner.save(sector)
        await self._invalidate(sector.tenant_id)

    async def delete(self, tenant_id: str, sector_id: str) -> None:
        await self._inner.delete(tenant_id, sector_id)
        await self._invalidate(tenant_id)


class CachedModifierRepository(_CachedRepository, ModifierRepository):
    """Modifier groups: the whole menu's groups are preloaded with the catalog
    so the waiter's chips render on tap."""

    _entity = "modifiers"

    def __init__(
        self,
        inner: ModifierRepository,
        cache: CachePort,
        ttl_seconds: int = CATALOG_TTL_SECONDS,
    ) -> None:
        super().__init__(cache, ttl_seconds)
        self._inner = inner

    async def list_for_product(
        self, tenant_id: str, product_id: str
    ) -> list[ModifierGroup]:
        key = await self._key(tenant_id, f"product:{product_id}")
        cached = await self._cache.get(key)
        if cached is not None:
            return list(cached)
        groups = await self._inner.list_for_product(tenant_id, product_id)
        await self._cache.set(key, list(groups), self._ttl)
        return groups

    async def list_for_products(
        self, tenant_id: str, product_ids: list[str]
    ) -> dict[str, list[ModifierGroup]]:
        if not product_ids:
            return {}
        key = await self._key(tenant_id, f"products:{','.join(sorted(set(product_ids)))}")
        cached = await self._cache.get(key)
        if cached is not None:
            return dict(cached)
        groups = await self._inner.list_for_products(tenant_id, product_ids)
        await self._cache.set(key, dict(groups), self._ttl)
        return groups

    async def replace_for_product(
        self, tenant_id: str, product_id: str, groups: list[ModifierGroup]
    ) -> None:
        await self._inner.replace_for_product(tenant_id, product_id, groups)
        await self._invalidate(tenant_id)
