"""Cross-aggregate consumption: when an order is PAID, discount the ingredients
of each item's recipe from stock. Idempotent and never blocks the sale."""

from __future__ import annotations

from uuid import uuid4

from app.application.inventory.ports import InventoryConsumer
from app.domain.identity.ports import TenantContext
from app.domain.inventory.entities import StockMovement
from app.domain.inventory.repository import (
    IngredientRepository,
    RecipeRepository,
    StockMovementRepository,
)
from app.domain.inventory.value_objects import MovementDirection, MovementReason
from app.domain.order.repository import OrderRepository


class ConsumeRecipesForOrder(InventoryConsumer):
    """Discount the recipes' ingredients for a PAID order.

    Idempotent: guarded by an existing SALE movement for the order, so a
    re-settle never double-discounts. A sale is never blocked by a shortage —
    stock may go negative (and surface in the low-stock alert) rather than
    failing the cobro. One aggregated OUT/SALE movement per ingredient.
    """

    def __init__(
        self,
        orders: OrderRepository,
        recipes: RecipeRepository,
        ingredients: IngredientRepository,
        movements: StockMovementRepository,
        tenant_context: TenantContext,
    ) -> None:
        self._orders = orders
        self._recipes = recipes
        self._ingredients = ingredients
        self._movements = movements
        self._tenant_context = tenant_context

    async def consume_for_order(self, tenant_id: str, order_id: str) -> None:
        self._tenant_context.set(tenant_id)
        if await self._movements.exists_for_order(tenant_id, order_id):
            return  # already consumed — idempotent no-op
        order = await self._orders.get_by_id(tenant_id, order_id)
        if order is None:
            return
        recipes = await self._recipes.list_for_products(
            tenant_id, [item.product_id for item in order.items]
        )
        if not recipes:
            return  # no product in this order has a recipe

        # Aggregate consumption per ingredient: Σ(item.quantity × recipe_qty).
        consumption: dict[str, int] = {}
        for item in order.items:
            recipe = recipes.get(item.product_id)
            if recipe is None:
                continue
            for recipe_item in recipe.items:
                consumption[recipe_item.ingredient_id] = (
                    consumption.get(recipe_item.ingredient_id, 0)
                    + item.quantity * recipe_item.qty
                )

        for ingredient_id, total_qty in consumption.items():
            if total_qty <= 0:
                continue
            ingredient = await self._ingredients.get_by_id(tenant_id, ingredient_id)
            if ingredient is None:
                continue  # ingredient deleted after the recipe was set — skip
            movement = StockMovement(
                id=str(uuid4()),
                tenant_id=tenant_id,
                ingredient_id=ingredient_id,
                direction=MovementDirection.OUT,
                reason=MovementReason.SALE,
                qty=total_qty,
                order_id=order_id,
            )
            ingredient.apply(movement)
            await self._movements.add(movement)
            await self._ingredients.save(ingredient)
