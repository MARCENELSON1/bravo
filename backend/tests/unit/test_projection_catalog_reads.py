"""La proyección de ventas no debe traer el catálogo entero por cada cobro.

Antes pedía `products.list(tenant_id)` (toda la carta) solo para un lookup de
categoría de las líneas de la orden: el costo de cada pago escalaba con el
tamaño del menú en vez del de la comanda.
"""

from __future__ import annotations

from datetime import date

from app.application.analytics.projection import ProjectOrderSales
from app.domain.advisor.repository import AdvisorSettingsRepository
from app.domain.inventory.recipe import Recipe
from app.domain.inventory.repository import (
    IngredientRepository,
    PreparationRepository,
    RecipeRepository,
)
from app.domain.order.entities import Order, OrderItem
from app.domain.order.repository import OrderRepository
from app.domain.order.value_objects import OrderStatus
from app.domain.product.entities import Product
from app.domain.product.repository import ProductRepository
from app.domain.shared.money import Money
from tests.fakes import FakeTenantContext

_TENANT = "t-1"


class _SpyProductRepository(ProductRepository):
    """Registra qué se le pidió, para distinguir catálogo entero vs. por ids."""

    def __init__(self, products: list[Product]) -> None:
        self.products = products
        self.calls: list[str] = []

    async def get_by_id(self, tenant_id: str, product_id: str) -> Product | None:
        return next((p for p in self.products if p.id == product_id), None)

    async def list(self, tenant_id: str, *, only_active: bool = False) -> list[Product]:
        self.calls.append("list")  # el catálogo COMPLETO
        return list(self.products)

    async def list_for_ids(self, tenant_id: str, product_ids: list[str]) -> list[Product]:
        self.calls.append(f"list_for_ids:{len(product_ids)}")
        wanted = set(product_ids)
        return [p for p in self.products if p.id in wanted]

    async def add(self, product: Product) -> None: ...

    async def save(self, product: Product) -> None: ...


class _OrderRepo(OrderRepository):
    def __init__(self, order: Order) -> None:
        self._order = order

    async def get_by_id(self, tenant_id: str, order_id: str) -> Order | None:
        return self._order

    async def add(self, order: Order) -> None: ...
    async def save(self, order: Order) -> None: ...
    async def list_by_status(self, tenant_id, status=None): return []
    async def list_kds(self, tenant_id, station=None): return []
    async def list_active(self, tenant_id): return []
    async def list_open_by_session(self, tenant_id, session_id): return []
    async def list_pending_qr(self, tenant_id): return []


class _NoRecipes(RecipeRepository):
    async def get_for_product(self, tenant_id: str, product_id: str) -> Recipe | None:
        return None

    async def list_for_products(self, tenant_id, product_ids) -> dict[str, Recipe]:
        return {}  # sin recetas: no hace falta insumos ni preparaciones

    async def save(self, recipe: Recipe) -> None: ...


class _Ingredients(IngredientRepository):
    def __init__(self) -> None:
        self.calls: list[str] = []

    async def get_by_id(self, tenant_id, ingredient_id): return None
    async def list_below_min(self, tenant_id): return []

    async def list(self, tenant_id, *, active_only: bool = False):
        self.calls.append("list")
        return []

    async def add(self, ingredient) -> None: ...
    async def save(self, ingredient) -> None: ...


class _Preparations(PreparationRepository):
    def __init__(self) -> None:
        self.calls: list[str] = []

    async def get(self, tenant_id, preparation_id): return None

    async def list(self, tenant_id):
        self.calls.append("list")
        return []

    async def usage_counts(self, tenant_id): return {}
    async def save(self, preparation) -> None: ...
    async def delete(self, tenant_id, preparation_id) -> None: ...


class _SaleFacts:
    def __init__(self) -> None:
        self.added: list = []

    async def exists_for_order(self, tenant_id: str, order_id: str) -> bool:
        return False

    async def add_many(self, facts: list) -> None:
        self.added.extend(facts)

    async def list_for_order(self, tenant_id: str, order_id: str) -> list:
        return []


class _Snapshots:
    async def add(self, tenant_id: str, day: date, **kwargs: int) -> None: ...


class _NoSettings(AdvisorSettingsRepository):
    async def get(self, tenant_id: str):
        return None

    async def save(self, settings) -> None: ...


def _order() -> Order:
    order = Order(
        id="o1",
        tenant_id=_TENANT,
        table_id="tb1",
        waiter_id="w1",
        currency="ARS",
        status=OrderStatus.PAID,
    )
    order.items = [
        OrderItem(
            id="i1",
            product_id="p1",
            name="Milanesa",
            unit_price=Money(1000, "ARS"),
            quantity=1,
        )
    ]
    return order


def _catalog(size: int) -> list[Product]:
    return [
        Product(
            id=f"p{n}",
            tenant_id=_TENANT,
            name=f"Product {n}",
            price=Money(1000, "ARS"),
            category="Principales",
        )
        for n in range(1, size + 1)
    ]


async def _project(products: _SpyProductRepository) -> _SaleFacts:
    facts = _SaleFacts()
    projector = ProjectOrderSales(
        orders=_OrderRepo(_order()),
        products=products,
        recipes=_NoRecipes(),
        ingredients=_Ingredients(),
        preparations=_Preparations(),
        sale_facts=facts,  # type: ignore[arg-type]
        snapshots=_Snapshots(),  # type: ignore[arg-type]
        advisor_settings=_NoSettings(),
        tenant_context=FakeTenantContext(),
    )
    await projector.project_order(_TENANT, "o1")
    return facts


async def test_asks_only_for_the_products_in_the_order() -> None:
    products = _SpyProductRepository(_catalog(50))

    await _project(products)

    # Una carta de 50 platos, una comanda de 1: se pide 1, no 50.
    assert products.calls == ["list_for_ids:1"]
    assert "list" not in products.calls


async def test_category_is_still_snapshotted_on_the_fact() -> None:
    # El refactor no cambia el resultado: la categoría sigue congelándose.
    products = _SpyProductRepository(_catalog(50))

    facts = await _project(products)

    assert len(facts.added) == 1
    assert facts.added[0].category == "Principales"


async def test_no_recipes_means_no_catalog_reads_at_all() -> None:
    ingredients, preparations = _Ingredients(), _Preparations()
    projector = ProjectOrderSales(
        orders=_OrderRepo(_order()),
        products=_SpyProductRepository(_catalog(10)),
        recipes=_NoRecipes(),
        ingredients=ingredients,
        preparations=preparations,
        sale_facts=_SaleFacts(),  # type: ignore[arg-type]
        snapshots=_Snapshots(),  # type: ignore[arg-type]
        advisor_settings=_NoSettings(),
        tenant_context=FakeTenantContext(),
    )

    await projector.project_order(_TENANT, "o1")

    # Sin recetas no se costea nada: insumos y preparaciones ni se tocan.
    assert ingredients.calls == []
    assert preparations.calls == []
