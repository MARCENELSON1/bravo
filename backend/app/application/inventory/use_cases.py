"""Inventory CRUD + stock movements (purchases / waste) + low-stock alerts.

Use cases depend on domain ports only and set the tenant context first so
Postgres RLS applies. Quantities are integers in milésimas of the base unit.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4

from app.domain.identity.ports import TenantContext
from app.domain.inventory.costing import weighted_unit_cost
from app.domain.inventory.entities import Ingredient, StockMovement, Supplier
from app.domain.inventory.exceptions import (
    IngredientNotFound,
    InvalidQuantity,
    InvalidUnitCost,
    PreparationNotFound,
    SupplierNotFound,
)
from app.domain.inventory.recipe import Recipe, RecipeItem
from app.domain.inventory.recipe_conversion import assert_convertible
from app.domain.inventory.repository import (
    IngredientRepository,
    PreparationRepository,
    RecipeRepository,
    StockMovementRepository,
    SupplierRepository,
)
from app.domain.inventory.value_objects import (
    FULL_YIELD_BPS,
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
        yield_pct: int = FULL_YIELD_BPS,
        price_includes_tax: bool = True,
        recipe_unit: str | None = None,
    ) -> Ingredient:
        self._tenant_context.set(tenant_id)
        tenant = await self._tenants.get_by_id(tenant_id)
        if tenant is None:
            raise TenantNotFound()
        if unit_cost_amount <= 0:
            raise InvalidUnitCost()
        if min_qty < 0 or stock_qty < 0:
            raise InvalidQuantity()
        base_unit = UnitOfMeasure(unit)
        recipe = UnitOfMeasure(recipe_unit) if recipe_unit else None
        assert_convertible(base_unit, recipe)  # raises IncompatibleUnits
        ingredient = Ingredient(
            id=str(uuid4()),
            tenant_id=tenant_id,
            name=name,
            unit=base_unit,
            stock_qty=stock_qty,
            min_qty=min_qty,
            unit_cost=Money(unit_cost_amount, tenant.currency),
            yield_pct=yield_pct,
            cost_includes_tax=price_includes_tax,
            recipe_unit=recipe,
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
        yield_pct: int | None = None,
        cost_includes_tax: bool | None = None,
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
        if yield_pct is not None:
            ingredient.yield_pct = yield_pct
        if cost_includes_tax is not None:
            ingredient.cost_includes_tax = cost_includes_tax
        await self._ingredients.save(ingredient)
        return ingredient


class RegisterPurchase:
    """Restock an ingredient: IN movement that raises stock and updates the unit
    cost by **weighted average (PPP)** — blends the stock you already had (at its
    cost) with what you bought (at its price), so a one-off expensive purchase
    doesn't inflate the whole food cost. With no prior stock it degrades to the
    purchase price (= last-cost). The movement still records the real price."""

    def __init__(
        self,
        ingredients: IngredientRepository,
        movements: StockMovementRepository,
        suppliers: SupplierRepository,
        tenant_context: TenantContext,
    ) -> None:
        self._ingredients = ingredients
        self._movements = movements
        self._suppliers = suppliers
        self._tenant_context = tenant_context

    async def execute(
        self,
        *,
        tenant_id: str,
        ingredient_id: str,
        qty: int,
        unit_cost_amount: int,
        price_includes_tax: bool | None = None,
        supplier_id: str | None = None,
    ) -> Ingredient:
        self._tenant_context.set(tenant_id)
        ingredient = await self._ingredients.get_by_id(tenant_id, ingredient_id)
        if ingredient is None:
            raise IngredientNotFound()
        if qty <= 0:
            raise InvalidQuantity()
        if unit_cost_amount <= 0:
            raise InvalidUnitCost()
        if supplier_id is not None:
            if await self._suppliers.get_by_id(tenant_id, supplier_id) is None:
                raise SupplierNotFound()
        # Solo reclasifica el IVA si el usuario lo indica; un restock no lo pisa.
        if price_includes_tax is not None:
            ingredient.cost_includes_tax = price_includes_tax
        unit_cost = Money(unit_cost_amount, ingredient.unit_cost.currency)
        movement = StockMovement(
            id=str(uuid4()),
            tenant_id=tenant_id,
            ingredient_id=ingredient_id,
            direction=MovementDirection.IN,
            reason=MovementReason.PURCHASE,
            qty=qty,
            unit_cost=unit_cost,  # el movimiento guarda el PRECIO REAL de la compra
            supplier_id=supplier_id,
        )
        # PPP: el costo del insumo = promedio ponderado del stock previo + la compra.
        # Se calcula con el stock ANTES de aplicar el IN (por eso va antes de apply).
        new_cost = weighted_unit_cost(
            ingredient.stock_qty, ingredient.unit_cost, qty, unit_cost
        )
        ingredient.apply(movement)
        ingredient.set_cost(new_cost)
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


def _supplier_phone(phone: str | None) -> str | None:
    """Solo dígitos (para el deep-link wa.me). Vacío → None."""
    if phone is None:
        return None
    digits = "".join(c for c in phone if c.isdigit())
    return digits or None


class CreateSupplier:
    def __init__(
        self, suppliers: SupplierRepository, tenant_context: TenantContext
    ) -> None:
        self._suppliers = suppliers
        self._tenant_context = tenant_context

    async def execute(
        self,
        *,
        tenant_id: str,
        name: str,
        contact: str | None = None,
        phone: str | None = None,
        notes: str | None = None,
    ) -> Supplier:
        self._tenant_context.set(tenant_id)
        supplier = Supplier(
            id=str(uuid4()),
            tenant_id=tenant_id,
            name=name,
            contact=contact,
            phone=_supplier_phone(phone),
            notes=notes,
        )
        await self._suppliers.add(supplier)
        return supplier


class UpdateSupplier:
    """Editar los datos de un proveedor (contacto/teléfono/notas/activo)."""

    def __init__(
        self, suppliers: SupplierRepository, tenant_context: TenantContext
    ) -> None:
        self._suppliers = suppliers
        self._tenant_context = tenant_context

    async def execute(
        self,
        *,
        tenant_id: str,
        supplier_id: str,
        name: str,
        contact: str | None,
        phone: str | None,
        notes: str | None,
        active: bool,
    ) -> Supplier:
        self._tenant_context.set(tenant_id)
        supplier = await self._suppliers.get_by_id(tenant_id, supplier_id)
        if supplier is None:
            raise SupplierNotFound()
        supplier.name = name
        supplier.contact = contact
        supplier.phone = _supplier_phone(phone)
        supplier.notes = notes
        supplier.active = active
        await self._suppliers.save(supplier)
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


@dataclass(frozen=True)
class SupplierPurchases:
    """Resumen de compras a un proveedor: cuánto le compraste, en cuántas compras
    y la última. Sobre movimientos PURCHASE con ese proveedor."""

    supplier_id: str
    currency: str
    total_spent: int  # minor units
    purchase_count: int
    last_purchase_at: datetime | None


class SupplierPurchasesReadModel(ABC):
    """Agregado de compras por proveedor. Scopeado por ``tenant_id``; solo lectura."""

    @abstractmethod
    async def summary(self, tenant_id: str, supplier_id: str) -> SupplierPurchases: ...


class GetSupplierPurchases:
    def __init__(
        self,
        suppliers: SupplierRepository,
        read_model: SupplierPurchasesReadModel,
        tenant_context: TenantContext,
    ) -> None:
        self._suppliers = suppliers
        self._read_model = read_model
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str, supplier_id: str) -> SupplierPurchases:
        self._tenant_context.set(tenant_id)
        if await self._suppliers.get_by_id(tenant_id, supplier_id) is None:
            raise SupplierNotFound()
        return await self._read_model.summary(tenant_id, supplier_id)


class SetRecipe:
    """Set (replace) a product's recipe — opt-in. Validates the product and the
    referenced ingredients exist for the tenant."""

    def __init__(
        self,
        recipes: RecipeRepository,
        products: ProductRepository,
        ingredients: IngredientRepository,
        preparations: PreparationRepository,
        tenant_context: TenantContext,
    ) -> None:
        self._recipes = recipes
        self._products = products
        self._ingredients = ingredients
        self._preparations = preparations
        self._tenant_context = tenant_context

    async def execute(
        self, *, tenant_id: str, product_id: str, items: list[RecipeItem]
    ) -> Recipe:
        self._tenant_context.set(tenant_id)
        product = await self._products.get_by_id(tenant_id, product_id)
        if product is None:
            raise ProductNotFound()
        known_ingredients = {i.id for i in await self._ingredients.list(tenant_id)}
        known_preparations = {p.id for p in await self._preparations.list(tenant_id)}
        for item in items:
            if item.ingredient_id is not None and item.ingredient_id not in known_ingredients:
                raise IngredientNotFound()
            if item.preparation_id is not None and item.preparation_id not in known_preparations:
                raise PreparationNotFound()
        # Fase 2D: versión incremental para atribución histórica (el food cost ya
        # se congela por venta). Receta nueva → v1; edición → versión previa + 1.
        current = await self._recipes.get_for_product(tenant_id, product_id)
        version = current.version + 1 if current is not None else 1
        recipe = Recipe(
            product_id=product_id, tenant_id=tenant_id, items=items, version=version
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
