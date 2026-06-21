"""Push projection: when an order is PAID, write its lines to the canonical
sale_facts (silver). Idempotent, snapshots food cost point-in-time."""

from __future__ import annotations

from uuid import uuid4

from app.application.analytics.facts import SaleFact
from app.application.analytics.ports import SaleFactsRepository, SalesProjector
from app.application.clock import utcnow
from app.domain.identity.ports import TenantContext
from app.domain.inventory.costing import food_cost as compute_food_cost
from app.domain.inventory.repository import IngredientRepository, RecipeRepository
from app.domain.order.repository import OrderRepository
from app.domain.order.value_objects import OrderStatus
from app.domain.product.repository import ProductRepository


class ProjectOrderSales(SalesProjector):
    """Project a PAID order's lines into sale_facts.

    Idempotent per order (guarded by existing facts). Snapshots the line's
    name/category/price and the recipe food cost at sale time (None when the
    product has no recipe). One ``SaleFact`` per order item.
    """

    def __init__(
        self,
        orders: OrderRepository,
        products: ProductRepository,
        recipes: RecipeRepository,
        ingredients: IngredientRepository,
        sale_facts: SaleFactsRepository,
        tenant_context: TenantContext,
    ) -> None:
        self._orders = orders
        self._products = products
        self._recipes = recipes
        self._ingredients = ingredients
        self._sale_facts = sale_facts
        self._tenant_context = tenant_context

    async def project_order(self, tenant_id: str, order_id: str) -> None:
        self._tenant_context.set(tenant_id)
        if await self._sale_facts.exists_for_order(tenant_id, order_id):
            return  # already projected — idempotent no-op
        order = await self._orders.get_by_id(tenant_id, order_id)
        if order is None or order.status is not OrderStatus.PAID:
            return
        if not order.items:
            return

        product_ids = [item.product_id for item in order.items]
        recipes = await self._recipes.list_for_products(tenant_id, product_ids)
        category_by_product = {
            product.id: product.category for product in await self._products.list(tenant_id)
        }
        cost_by_ingredient = (
            {ing.id: ing.unit_cost for ing in await self._ingredients.list(tenant_id)}
            if recipes
            else {}
        )
        occurred_at = utcnow()

        facts: list[SaleFact] = []
        for item in order.items:
            recipe = recipes.get(item.product_id)
            food_cost_amount: int | None = None
            if recipe is not None:
                per_unit = compute_food_cost(recipe.items, cost_by_ingredient, order.currency)
                food_cost_amount = per_unit.amount * item.quantity
            facts.append(
                SaleFact(
                    id=str(uuid4()),
                    tenant_id=tenant_id,
                    order_id=order_id,
                    order_item_id=item.id,
                    product_id=item.product_id,
                    product_name=item.name,
                    category=category_by_product.get(item.product_id),
                    quantity=item.quantity,
                    unit_price_amount=item.unit_price.amount,
                    line_amount=item.unit_price.amount * item.quantity,
                    food_cost_amount=food_cost_amount,
                    currency=order.currency,
                    waiter_id=order.waiter_id,
                    table_id=order.table_id,
                    occurred_at=occurred_at,
                )
            )
        await self._sale_facts.add_many(facts)
