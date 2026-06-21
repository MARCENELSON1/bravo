from __future__ import annotations

from sqlalchemy import select

from app.application.inventory.food_cost import (
    FoodCostReadModel,
    FoodCostReport,
    FoodCostRow,
)
from app.domain.inventory.costing import (
    food_cost as compute_food_cost,
)
from app.domain.inventory.costing import (
    food_cost_ratio_bps,
    margin,
)
from app.domain.inventory.recipe import RecipeItem
from app.domain.shared.money import Money
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.models import (
    IngredientORM,
    ProductORM,
    RecipeItemORM,
    TenantORM,
)


class SqlAlchemyFoodCostReadModel(FoodCostReadModel):
    """Per-product food cost computed in Python with the domain costing
    functions (single source of truth). Only products that have recipe items are
    returned. Tenant-scoped (RLS + explicit filter); read-only."""

    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def food_cost(self, tenant_id: str) -> FoodCostReport:
        async with self._session_factory() as session:
            currency_row = (
                await session.execute(
                    select(TenantORM.currency).where(TenantORM.id == tenant_id)
                )
            ).scalar_one_or_none()
            currency = currency_row if currency_row is not None else "ARS"

            products = {
                pid: (name, price_amount, price_currency)
                for pid, name, price_amount, price_currency in (
                    await session.execute(
                        select(
                            ProductORM.id,
                            ProductORM.name,
                            ProductORM.price_amount,
                            ProductORM.price_currency,
                        ).where(ProductORM.tenant_id == tenant_id)
                    )
                ).all()
            }

            cost_by_ingredient = {
                iid: Money(amount, cur)
                for iid, amount, cur in (
                    await session.execute(
                        select(
                            IngredientORM.id,
                            IngredientORM.unit_cost_amount,
                            IngredientORM.unit_cost_currency,
                        ).where(IngredientORM.tenant_id == tenant_id)
                    )
                ).all()
            }

            items_by_product: dict[str, list[RecipeItem]] = {}
            for product_id, ingredient_id, qty in (
                await session.execute(
                    select(
                        RecipeItemORM.product_id,
                        RecipeItemORM.ingredient_id,
                        RecipeItemORM.qty,
                    ).where(RecipeItemORM.tenant_id == tenant_id)
                )
            ).all():
                items_by_product.setdefault(product_id, []).append(
                    RecipeItem(ingredient_id=ingredient_id, qty=qty)
                )

            rows: list[FoodCostRow] = []
            for product_id, items in items_by_product.items():
                product = products.get(product_id)
                if product is None:
                    continue
                name, price_amount, price_currency = product
                price = Money(price_amount, price_currency)
                fc = compute_food_cost(items, cost_by_ingredient, price_currency)
                rows.append(
                    FoodCostRow(
                        product_id=product_id,
                        product_name=name,
                        price_amount=price.amount,
                        food_cost_amount=fc.amount,
                        margin_amount=margin(price, fc),
                        food_cost_ratio_bps=food_cost_ratio_bps(price, fc),
                        currency=price_currency,
                    )
                )
            rows.sort(key=lambda r: r.product_name)
            return FoodCostReport(currency=currency, rows=rows)
