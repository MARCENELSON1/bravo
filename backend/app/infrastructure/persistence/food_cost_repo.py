from __future__ import annotations

from sqlalchemy import select

from app.application.inventory.food_cost import (
    FoodCostReadModel,
    FoodCostReport,
    FoodCostRow,
)
from app.domain.inventory.costing import (
    coverage_bps as compute_coverage_bps,
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
from app.domain.inventory.value_objects import (
    CONFIRMED_PLATE_BPS,
    COVERAGE_GATE_BPS,
    FOOD_COST_SANE_MAX_BPS,
    FOOD_COST_SANE_MIN_BPS,
    MovementReason,
    UnitOfMeasure,
)
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
    StockMovementORM,
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
                    UnitOfMeasure.parse(r.unit),
                    UnitOfMeasure.parse(r.recipe_unit) if r.recipe_unit else None,
                )
                for r in ingredient_rows
            }
            # Fase 3: un insumo está "confirmado" si tiene ≥1 compra real cargada
            # (movimiento PURCHASE). El costo solo se mueve por compra → derivación
            # exacta, sin flag ni migración. Tenant-scoped + RLS.
            confirmed_ids = set(
                (
                    await session.execute(
                        select(StockMovementORM.ingredient_id)
                        .where(
                            StockMovementORM.tenant_id == tenant_id,
                            StockMovementORM.reason == MovementReason.PURCHASE.value,
                        )
                        .distinct()
                    )
                ).scalars().all()
            )
            # Costo confirmado por insumo (bruto): el costo si tiene compra, si no 0
            # (no cuenta a la cobertura). La cobertura del plato = confirmado/bruto.
            confirmed_cost_by_ingredient = {
                r.id: (
                    cost_by_ingredient[r.id]
                    if r.id in confirmed_ids
                    else Money(0, r.unit_cost_currency)
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
                # Fase 3: preparación confirmada = componentes confirmados (los no
                # confirmados aportan 0 al costo confirmado, igual que el mapa neto).
                confirmed_cost_by_preparation = resolve_preparation_costs(
                    preparations,
                    confirmed_cost_by_ingredient,
                    currency,
                    factor_by_ingredient=factor_by_ingredient,
                )
            except RecipeCycle:
                cost_by_preparation = {}
                net_cost_by_preparation = {}
                confirmed_cost_by_preparation = {}

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
                # Fase 3: costo confirmado (solo insumos con compra real) → cobertura
                # = confirmado / bruto. Un plato es confirmado si la cobertura es
                # total. NO afecta food_cost_amount/margen (se agregan campos).
                confirmed_fc = compute_food_cost(
                    items,
                    confirmed_cost_by_ingredient,
                    price_currency,
                    cost_by_preparation=confirmed_cost_by_preparation,
                    factor_by_ingredient=factor_by_ingredient,
                )
                coverage = compute_coverage_bps(confirmed_fc, gross_fc)
                # El food cost se muestra BRUTO (COGS real). El margen ("te deja") y
                # el ratio (food cost %) son NETOS: precio neto − costo neto. El
                # precio se muestra bruto (lo que cobra el dueño). Con VAT 0, neto ==
                # bruto (paridad).
                net_price = Money(net_of_vat(price.amount, vat_bps), price_currency)
                ratio = food_cost_ratio_bps(net_price, net_fc)
                rows.append(
                    FoodCostRow(
                        product_id=product_id,
                        product_name=name,
                        price_amount=price.amount,
                        food_cost_amount=gross_fc.amount,
                        margin_amount=margin(net_price, net_fc),
                        food_cost_ratio_bps=ratio,
                        currency=price_currency,
                        cost_confirmed=coverage >= CONFIRMED_PLATE_BPS,
                        coverage_bps=coverage,
                        # Guarda de sanidad: ratio fuera de [5%, 95%] → "revisar".
                        ratio_sane=FOOD_COST_SANE_MIN_BPS <= ratio <= FOOD_COST_SANE_MAX_BPS,
                    )
                )
            rows.sort(key=lambda r: r.product_name)
            total_count = len(rows)
            confirmed_count = sum(1 for r in rows if r.cost_confirmed)
            report_coverage = (
                round(confirmed_count * 10000 / total_count) if total_count else 10000
            )
            return FoodCostReport(
                currency=currency,
                rows=rows,
                coverage_bps=report_coverage,
                confirmed_count=confirmed_count,
                total_count=total_count,
                coverage_ok=report_coverage >= COVERAGE_GATE_BPS,
            )
