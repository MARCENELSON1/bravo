from __future__ import annotations

from sqlalchemy import select

from app.application.inventory.food_cost import (
    FoodCostReadModel,
    FoodCostReport,
    FoodCostRow,
)
from app.domain.inventory.costing import (
    effective_unit_cost,
    food_cost_ratio_bps,
    margin,
    net_effective_unit_cost,
    resolve_preparation_costs,
)
from app.domain.inventory.costing import (
    food_cost as compute_food_cost,
)
from app.domain.inventory.exceptions import RecipeCycle
from app.domain.inventory.recipe import RecipeItem
from app.domain.inventory.recipe_conversion import conversion_factor
from app.domain.inventory.value_objects import UnitOfMeasure
from app.domain.shared.money import Money
from app.domain.shared.vat import net_of_vat
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.mappers import preparation_to_domain
from app.infrastructure.persistence.models import (
    AdvisorSettingsORM,
    IngredientORM,
    PreparationItemORM,
    PreparationORM,
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

            # IVA global del tenant (bps): netea precio y costo para el margen real.
            # 0 = sin cargar → net_of_vat es identidad → paridad total.
            vat_bps = (
                await session.execute(
                    select(AdvisorSettingsORM.default_vat_bps).where(
                        AdvisorSettingsORM.tenant_id == tenant_id
                    )
                )
            ).scalar_one_or_none() or 0

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

            # Dos costos por insumo: bruto (merma/yield, COGS real) y neto de IVA
            # per-insumo según su flag cost_includes_tax. El food cost se MUESTRA
            # bruto (consistente con Asesor/Finanzas); el margen/ratio usan el neto.
            # Con vat_bps 0 → neto == bruto (paridad).
            ingredient_rows = (
                await session.execute(
                    select(
                        IngredientORM.id,
                        IngredientORM.unit_cost_amount,
                        IngredientORM.unit_cost_currency,
                        IngredientORM.yield_pct,
                        IngredientORM.cost_includes_tax,
                        IngredientORM.unit,
                        IngredientORM.recipe_unit,
                    ).where(IngredientORM.tenant_id == tenant_id)
                )
            ).all()
            cost_by_ingredient = {
                r.id: effective_unit_cost(
                    Money(r.unit_cost_amount, r.unit_cost_currency), r.yield_pct
                )
                for r in ingredient_rows
            }
            net_cost_by_ingredient = {
                r.id: net_effective_unit_cost(
                    Money(r.unit_cost_amount, r.unit_cost_currency),
                    r.yield_pct,
                    r.cost_includes_tax,
                    vat_bps,
                )
                for r in ingredient_rows
            }
            # Fase 2C: factor de conversión unidad de receta → unidad base por insumo.
            factor_by_ingredient = {
                r.id: conversion_factor(
                    UnitOfMeasure(r.unit),
                    UnitOfMeasure(r.recipe_unit) if r.recipe_unit else None,
                )
                for r in ingredient_rows
            }

            items_by_product: dict[str, list[RecipeItem]] = {}
            for row in (
                await session.execute(
                    select(RecipeItemORM).where(RecipeItemORM.tenant_id == tenant_id)
                )
            ).scalars().all():
                item = (
                    RecipeItem(preparation_id=row.preparation_id, qty=row.qty)
                    if row.preparation_id is not None
                    else RecipeItem(ingredient_id=row.ingredient_id, qty=row.qty)
                )
                items_by_product.setdefault(row.product_id, []).append(item)

            # Preparaciones (recetas madre) → costo por unidad, multinivel.
            prep_rows = (
                await session.execute(
                    select(PreparationORM).where(PreparationORM.tenant_id == tenant_id)
                )
            ).scalars().all()
            prep_items_by_prep: dict[str, list[PreparationItemORM]] = {}
            for pi in (
                await session.execute(
                    select(PreparationItemORM).where(
                        PreparationItemORM.tenant_id == tenant_id
                    )
                )
            ).scalars().all():
                prep_items_by_prep.setdefault(pi.preparation_id, []).append(pi)
            preparations = {
                r.id: preparation_to_domain(r, prep_items_by_prep.get(r.id, []))
                for r in prep_rows
            }
            try:
                cost_by_preparation = resolve_preparation_costs(
                    preparations,
                    cost_by_ingredient,
                    currency,
                    factor_by_ingredient=factor_by_ingredient,
                )
                # Con VAT 0 el mapa neto es idéntico al bruto → se reusa.
                net_cost_by_preparation = (
                    cost_by_preparation
                    if vat_bps == 0
                    else resolve_preparation_costs(
                        preparations,
                        net_cost_by_ingredient,
                        currency,
                        factor_by_ingredient=factor_by_ingredient,
                    )
                )
            except RecipeCycle:
                cost_by_preparation = {}
                net_cost_by_preparation = {}

            rows: list[FoodCostRow] = []
            for product_id, items in items_by_product.items():
                product = products.get(product_id)
                if product is None:
                    continue
                name, price_amount, price_currency = product
                price = Money(price_amount, price_currency)
                gross_fc = compute_food_cost(
                    items,
                    cost_by_ingredient,
                    price_currency,
                    cost_by_preparation=cost_by_preparation,
                    factor_by_ingredient=factor_by_ingredient,
                )
                net_fc = compute_food_cost(
                    items,
                    net_cost_by_ingredient,
                    price_currency,
                    cost_by_preparation=net_cost_by_preparation,
                    factor_by_ingredient=factor_by_ingredient,
                )
                # El food cost se muestra BRUTO (COGS real). El margen ("te deja") y
                # el ratio (food cost %) son NETOS: precio neto − costo neto. El
                # precio se muestra bruto (lo que cobra el dueño). Con VAT 0, neto ==
                # bruto (paridad).
                net_price = Money(net_of_vat(price.amount, vat_bps), price_currency)
                rows.append(
                    FoodCostRow(
                        product_id=product_id,
                        product_name=name,
                        price_amount=price.amount,
                        food_cost_amount=gross_fc.amount,
                        margin_amount=margin(net_price, net_fc),
                        food_cost_ratio_bps=food_cost_ratio_bps(net_price, net_fc),
                        currency=price_currency,
                    )
                )
            rows.sort(key=lambda r: r.product_name)
            return FoodCostReport(currency=currency, rows=rows)
