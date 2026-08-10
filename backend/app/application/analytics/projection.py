"""Push projection: when an order is PAID, write its lines to the canonical
sale_facts (silver). Idempotent, snapshots food cost point-in-time."""

from __future__ import annotations

from uuid import uuid4

from app.application.analytics.facts import SaleFact
from app.application.analytics.ports import (
    FinanceSnapshotWriter,
    SaleFactsRepository,
    SalesProjector,
)
from app.application.clock import utcnow
from app.domain.advisor.repository import AdvisorSettingsRepository
from app.domain.identity.ports import TenantContext
from app.domain.inventory.costing import food_cost as compute_food_cost
from app.domain.inventory.costing import net_effective_unit_cost, resolve_preparation_costs
from app.domain.inventory.exceptions import RecipeCycle
from app.domain.inventory.recipe_conversion import conversion_factor
from app.domain.inventory.repository import (
    IngredientRepository,
    PreparationRepository,
    RecipeRepository,
)
from app.domain.order.repository import OrderRepository
from app.domain.order.value_objects import OrderStatus
from app.domain.product.repository import ProductRepository
from app.domain.shared.vat import net_of_vat


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
        preparations: PreparationRepository,
        sale_facts: SaleFactsRepository,
        snapshots: FinanceSnapshotWriter,
        advisor_settings: AdvisorSettingsRepository,
        tenant_context: TenantContext,
    ) -> None:
        self._orders = orders
        self._products = products
        self._recipes = recipes
        self._ingredients = ingredients
        self._preparations = preparations
        self._sale_facts = sale_facts
        self._snapshots = snapshots
        self._advisor_settings = advisor_settings
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
        # Solución 1: se congelan en la proyección los netos de IVA (ventas y food)
        # además de los brutos, para que el margen agregado sea siempre "ventas
        # netas − food neto" sin re-netear en lectura (simétrico y estable si luego
        # cambia el IVA). El food neto respeta cost_includes_tax de cada insumo. Con
        # default_vat_bps 0 el neto = bruto (paridad, nada cambia en vivo).
        settings = await self._advisor_settings.get(tenant_id)
        vat_bps = settings.default_vat_bps if settings else 0

        cost_by_ingredient: dict = {}
        cost_net_by_ingredient: dict = {}
        factor_by_ingredient: dict = {}  # Fase 2C: unidad de receta → base
        if recipes:
            for ing in await self._ingredients.list(tenant_id):
                cost_by_ingredient[ing.id] = ing.effective_unit_cost
                cost_net_by_ingredient[ing.id] = net_effective_unit_cost(
                    ing.unit_cost, ing.yield_pct, ing.cost_includes_tax, vat_bps
                )
                factor_by_ingredient[ing.id] = conversion_factor(
                    ing.unit, ing.recipe_unit
                )
        # Costo por unidad de cada preparación (receta madre), multinivel, bruto y
        # neto. Un ciclo no debe romper el cobro → se degrada a "sin preparaciones".
        # Con VAT 0 el mapa neto es idéntico al bruto → se reusa (una sola pasada).
        cost_by_preparation: dict = {}
        cost_net_by_preparation: dict = {}
        if recipes:
            preparations = {p.id: p for p in await self._preparations.list(tenant_id)}
            if preparations:
                try:
                    cost_by_preparation = resolve_preparation_costs(
                        preparations,
                        cost_by_ingredient,
                        order.currency,
                        factor_by_ingredient=factor_by_ingredient,
                    )
                    cost_net_by_preparation = (
                        cost_by_preparation
                        if vat_bps == 0
                        else resolve_preparation_costs(
                            preparations,
                            cost_net_by_ingredient,
                            order.currency,
                            factor_by_ingredient=factor_by_ingredient,
                        )
                    )
                except RecipeCycle:
                    cost_by_preparation = {}
                    cost_net_by_preparation = {}
        occurred_at = utcnow()

        facts: list[SaleFact] = []
        for item in order.items:
            recipe = recipes.get(item.product_id)
            food_cost_amount: int | None = None
            food_cost_net_amount: int | None = None
            if recipe is not None:
                per_unit = compute_food_cost(
                    recipe.items,
                    cost_by_ingredient,
                    order.currency,
                    cost_by_preparation=cost_by_preparation,
                    factor_by_ingredient=factor_by_ingredient,
                )
                per_unit_net = compute_food_cost(
                    recipe.items,
                    cost_net_by_ingredient,
                    order.currency,
                    cost_by_preparation=cost_net_by_preparation,
                    factor_by_ingredient=factor_by_ingredient,
                )
                food_cost_amount = per_unit.amount * item.quantity
                food_cost_net_amount = per_unit_net.amount * item.quantity
            line_amount = item.unit_price.amount * item.quantity
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
                    line_amount=line_amount,
                    line_net_amount=net_of_vat(line_amount, vat_bps),
                    food_cost_amount=food_cost_amount,
                    food_cost_net_amount=food_cost_net_amount,
                    recipe_version=recipe.version if recipe is not None else None,
                    currency=order.currency,
                    waiter_id=order.waiter_id,
                    table_id=order.table_id,
                    occurred_at=occurred_at,
                )
            )
        await self._sale_facts.add_many(facts)
        # Tanda F: mantener el snapshot diario incremental (co-locado con la
        # escritura de sale_facts). Una orden proyecta en un solo instante → un día.
        await self._snapshots.add(
            tenant_id,
            occurred_at.date(),
            sales_amount=sum(f.line_amount for f in facts),
            sales_net_amount=sum(f.line_net_amount or 0 for f in facts),
            food_cost_amount=sum(f.food_cost_amount or 0 for f in facts),
            food_cost_net_amount=sum(f.food_cost_net_amount or 0 for f in facts),
            orders_count=1,
            units_sold=sum(f.quantity for f in facts),
        )

    async def reverse_order(self, tenant_id: str, order_id: str) -> None:
        """Drop the order's sale_facts so a reopen leaves no revenue behind.
        Idempotent (delete-if-present); the facts re-project on the next PAID."""
        self._tenant_context.set(tenant_id)
        facts = await self._sale_facts.list_for_order(tenant_id, order_id)
        if facts:
            # Decrementar el snapshot del día antes de borrar los facts.
            await self._snapshots.add(
                tenant_id,
                facts[0].occurred_at.date(),
                sales_amount=-sum(f.line_amount for f in facts),
                sales_net_amount=-sum(f.line_net_amount or 0 for f in facts),
                food_cost_amount=-sum(f.food_cost_amount or 0 for f in facts),
                food_cost_net_amount=-sum(f.food_cost_net_amount or 0 for f in facts),
                orders_count=-1,
                units_sold=-sum(f.quantity for f in facts),
            )
        await self._sale_facts.delete_for_order(tenant_id, order_id)
