from __future__ import annotations

from app.domain.product.entities import Product
from app.domain.product.repository import ProductRepository
from app.domain.shared.money import Money
from app.infrastructure.cache.cached_repositories import CachedProductRepository
from app.infrastructure.cache.memory_cache import InMemoryCache


def _product(product_id: str = "p1", tenant_id: str = "t-1", price: int = 1000) -> Product:
    return Product(
        id=product_id,
        tenant_id=tenant_id,
        name=f"Product {product_id}",
        price=Money(price, "ARS"),
    )


class _CountingProductRepository(ProductRepository):
    """Records every call so the tests can assert what actually hit the DB."""

    def __init__(self, products: list[Product] | None = None) -> None:
        self.products = products if products is not None else [_product()]
        self.calls: list[str] = []

    async def get_by_id(self, tenant_id: str, product_id: str) -> Product | None:
        self.calls.append(f"get_by_id:{product_id}")
        return next((p for p in self.products if p.id == product_id), None)

    async def list(self, tenant_id: str, *, only_active: bool = False) -> list[Product]:
        self.calls.append(f"list:active={only_active}")
        return [p for p in self.products if p.tenant_id == tenant_id]

    async def list_for_ids(self, tenant_id: str, product_ids: list[str]) -> list[Product]:
        self.calls.append(f"list_for_ids:{sorted(product_ids)}")
        wanted = set(product_ids)
        return [p for p in self.products if p.tenant_id == tenant_id and p.id in wanted]

    async def add(self, product: Product) -> None:
        self.calls.append("add")
        self.products.append(product)

    async def save(self, product: Product) -> None:
        self.calls.append("save")
        self.products = [p for p in self.products if p.id != product.id] + [product]


async def test_second_list_is_served_from_cache() -> None:
    inner = _CountingProductRepository()
    repo = CachedProductRepository(inner, InMemoryCache())

    first = await repo.list("t-1")
    second = await repo.list("t-1")

    assert first == second
    assert inner.calls == ["list:active=False"]  # el segundo no pegó a la DB


async def test_save_invalidates_so_the_new_price_is_read() -> None:
    inner = _CountingProductRepository()
    repo = CachedProductRepository(inner, InMemoryCache())
    await repo.list("t-1")  # warm

    await repo.save(_product(price=9999))
    products = await repo.list("t-1")

    # Nunca se sirve un precio viejo después de editar.
    assert products[0].price.amount == 9999
    assert inner.calls == ["list:active=False", "save", "list:active=False"]


async def test_add_also_invalidates() -> None:
    inner = _CountingProductRepository()
    repo = CachedProductRepository(inner, InMemoryCache())
    await repo.list("t-1")

    await repo.add(_product("p2"))
    products = await repo.list("t-1")

    assert {p.id for p in products} == {"p1", "p2"}


async def test_only_active_is_cached_separately() -> None:
    inner = _CountingProductRepository()
    repo = CachedProductRepository(inner, InMemoryCache())

    await repo.list("t-1", only_active=False)
    await repo.list("t-1", only_active=True)

    # Distinta pregunta → distinta key, no se contamina una con la otra.
    assert inner.calls == ["list:active=False", "list:active=True"]


async def test_cache_is_isolated_between_tenants() -> None:
    inner = _CountingProductRepository(
        [_product("p1", "t-1"), _product("p2", "t-2")]
    )
    repo = CachedProductRepository(inner, InMemoryCache())

    assert [p.id for p in await repo.list("t-1")] == ["p1"]
    assert [p.id for p in await repo.list("t-2")] == ["p2"]

    # Una escritura de un tenant no invalida (ni expone) la caché del otro.
    await repo.save(_product("p1", "t-1", price=5))
    inner.calls.clear()
    await repo.list("t-2")
    assert inner.calls == []  # t-2 sigue cacheado


async def test_mutating_the_returned_list_does_not_poison_the_cache() -> None:
    inner = _CountingProductRepository()
    repo = CachedProductRepository(inner, InMemoryCache())

    first = await repo.list("t-1")
    first.clear()  # un caller descuidado

    assert len(await repo.list("t-1")) == 1


async def test_list_for_ids_short_circuits_on_empty() -> None:
    inner = _CountingProductRepository()
    repo = CachedProductRepository(inner, InMemoryCache())

    assert await repo.list_for_ids("t-1", []) == []
    assert inner.calls == []  # ni cache ni DB
