"""Inventory CRUD + stock movements (purchases / waste) + low-stock alerts.

Use cases depend on domain ports only and set the tenant context first so
Postgres RLS applies. Quantities are integers in milésimas of the base unit.
"""

from __future__ import annotations

from uuid import uuid4

from app.domain.identity.ports import TenantContext
from app.domain.inventory.entities import Ingredient, StockMovement, Supplier
from app.domain.inventory.exceptions import (
    IngredientNotFound,
    InvalidQuantity,
    InvalidUnitCost,
)
from app.domain.inventory.recipe import Recipe, RecipeItem
from app.domain.inventory.repository import (
    IngredientRepository,
    RecipeRepository,
    StockMovementRepository,
    SupplierRepository,
)
from app.domain.inventory.value_objects import (
    MovementDirection,
    MovementReason,
    UnitOfMeasure,
)
from app.domain.product.exceptions import ProductNotFound
from app.domain.product.repository import ProductRepository
from app.domain.shared.money import Money
from app.domain.tenant.exceptions import TenantNotFound
from app.domain.tenant.repository import TenantRepository


class CreateIngredient:
    """Create an inventory item priced in the tenant's currency."""

    def __init__(
        self,
        ingredients: IngredientRepository,
        tenants: TenantRepository,
        tenant_context: TenantContext,
    ) -> None:
        self._ingredients = ingredients
        self._tenants = tenants
        self._tenant_context = tenant_context

    async def execute(
        self,
        *,
        tenant_id: str,
        name: str,
        unit: str,
        min_qty: int,
        unit_cost_amount: int,
        stock_qty: int = 0,
    ) -> Ingredient:
        self._tenant_context.set(tenant_id)
        tenant = await self._tenants.get_by_id(tenant_id)
        if tenant is None:
            raise TenantNotFound()
        if unit_cost_amount <= 0:
            raise InvalidUnitCost()
        if min_qty < 0 or stock_qty < 0:
            raise InvalidQuantity()
        ingredient = Ingredient(
            id=str(uuid4()),
            tenant_id=tenant_id,
            name=name,
            unit=UnitOfMeasure(unit),
            stock_qty=stock_qty,
            min_qty=min_qty,
            unit_cost=Money(unit_cost_amount, tenant.currency),
        )
        await self._ingredients.add(ingredient)
        return ingredient


class ListIngredients:
    def __init__(
        self, ingredients: IngredientRepository, tenant_context: TenantContext
    ) -> None:
        self._ingredients = ingredients
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str, active_only: bool = False) -> list[Ingredient]:
        self._tenant_context.set(tenant_id)
        return await self._ingredients.list(tenant_id, active_only=active_only)


class UpdateIngredient:
    """Edit an ingredient's name, minimum or active flag (cost moves via purchases)."""

    def __init__(
        self, ingredients: IngredientRepository, tenant_context: TenantContext
    ) -> None:
        self._ingredients = ingredients
        self._tenant_context = tenant_context

    async def execute(
        self,
        *,
        tenant_id: str,
        ingredient_id: str,
        name: str | None = None,
        min_qty: int | None = None,
        active: bool | None = None,
    ) -> Ingredient:
        self._tenant_context.set(tenant_id)
        ingredient = await self._ingredients.get_by_id(tenant_id, ingredient_id)
        if ingredient is None:
            raise IngredientNotFound()
        if name is not None:
            ingredient.name = name
        if min_qty is not None:
            if min_qty < 0:
                raise InvalidQuantity()
            ingredient.min_qty = min_qty
        if active is not None:
            ingredient.active = active
        await self._ingredients.save(ingredient)
        return ingredient


class RegisterPurchase:
    """Restock an ingredient: IN movement that raises stock and updates the
    unit cost (last-cost policy)."""

    def __init__(
        self,
        ingredients: IngredientRepository,
        movements: StockMovementRepository,
        tenant_context: TenantContext,
    ) -> None:
        self._ingredients = ingredients
        self._movements = movements
        self._tenant_context = tenant_context

    async def execute(
        self, *, tenant_id: str, ingredient_id: str, qty: int, unit_cost_amount: int
    ) -> Ingredient:
        self._tenant_context.set(tenant_id)
        ingredient = await self._ingredients.get_by_id(tenant_id, ingredient_id)
        if ingredient is None:
            raise IngredientNotFound()
        if qty <= 0:
            raise InvalidQuantity()
        if unit_cost_amount <= 0:
            raise InvalidUnitCost()
        unit_cost = Money(unit_cost_amount, ingredient.unit_cost.currency)
        movement = StockMovement(
            id=str(uuid4()),
            tenant_id=tenant_id,
            ingredient_id=ingredient_id,
            direction=MovementDirection.IN,
            reason=MovementReason.PURCHASE,
            qty=qty,
            unit_cost=unit_cost,
        )
        ingredient.apply(movement)
        ingredient.set_cost(unit_cost)
        await self._movements.add(movement)
        await self._ingredients.save(ingredient)
        return ingredient


class RegisterWaste:
    """Register a merma: OUT movement that lowers stock (stock may go negative)."""

    def __init__(
        self,
        ingredients: IngredientRepository,
        movements: StockMovementRepository,
        tenant_context: TenantContext,
    ) -> None:
        self._ingredients = ingredients
        self._movements = movements
        self._tenant_context = tenant_context

    async def execute(
        self, *, tenant_id: str, ingredient_id: str, qty: int, note: str | None = None
    ) -> Ingredient:
        self._tenant_context.set(tenant_id)
        ingredient = await self._ingredients.get_by_id(tenant_id, ingredient_id)
        if ingredient is None:
            raise IngredientNotFound()
        if qty <= 0:
            raise InvalidQuantity()
        movement = StockMovement(
            id=str(uuid4()),
            tenant_id=tenant_id,
            ingredient_id=ingredient_id,
            direction=MovementDirection.OUT,
            reason=MovementReason.WASTE,
            qty=qty,
            note=note,
        )
        ingredient.apply(movement)
        await self._movements.add(movement)
        await self._ingredients.save(ingredient)
        return ingredient


class ListLowStock:
    """Ingredients at or below their minimum (quiebre alerts)."""

    def __init__(
        self, ingredients: IngredientRepository, tenant_context: TenantContext
    ) -> None:
        self._ingredients = ingredients
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str) -> list[Ingredient]:
        self._tenant_context.set(tenant_id)
        return await self._ingredients.list_below_min(tenant_id)


class CreateSupplier:
    def __init__(
        self, suppliers: SupplierRepository, tenant_context: TenantContext
    ) -> None:
        self._suppliers = suppliers
        self._tenant_context = tenant_context

    async def execute(
        self, *, tenant_id: str, name: str, contact: str | None = None
    ) -> Supplier:
        self._tenant_context.set(tenant_id)
        supplier = Supplier(
            id=str(uuid4()), tenant_id=tenant_id, name=name, contact=contact
        )
        await self._suppliers.add(supplier)
        return supplier


class ListSuppliers:
    def __init__(
        self, suppliers: SupplierRepository, tenant_context: TenantContext
    ) -> None:
        self._suppliers = suppliers
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str, active_only: bool = False) -> list[Supplier]:
        self._tenant_context.set(tenant_id)
        return await self._suppliers.list(tenant_id, active_only=active_only)


class SetRecipe:
    """Set (replace) a product's recipe — opt-in. Validates the product and the
    referenced ingredients exist for the tenant."""

    def __init__(
        self,
        recipes: RecipeRepository,
        products: ProductRepository,
        ingredients: IngredientRepository,
        tenant_context: TenantContext,
    ) -> None:
        self._recipes = recipes
        self._products = products
        self._ingredients = ingredients
        self._tenant_context = tenant_context

    async def execute(
        self, *, tenant_id: str, product_id: str, items: list[tuple[str, int]]
    ) -> Recipe:
        self._tenant_context.set(tenant_id)
        product = await self._products.get_by_id(tenant_id, product_id)
        if product is None:
            raise ProductNotFound()
        known = {i.id for i in await self._ingredients.list(tenant_id)}
        for ingredient_id, _qty in items:
            if ingredient_id not in known:
                raise IngredientNotFound()
        recipe = Recipe(
            product_id=product_id,
            tenant_id=tenant_id,
            items=[RecipeItem(ingredient_id=iid, qty=qty) for iid, qty in items],
        )
        await self._recipes.save(recipe)
        return recipe


class GetRecipe:
    def __init__(self, recipes: RecipeRepository, tenant_context: TenantContext) -> None:
        self._recipes = recipes
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str, product_id: str) -> Recipe | None:
        self._tenant_context.set(tenant_id)
        return await self._recipes.get_for_product(tenant_id, product_id)
