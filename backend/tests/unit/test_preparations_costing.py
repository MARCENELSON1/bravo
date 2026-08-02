"""Productos v2 Tanda C — food cost multinivel con recetas madre (unit, sin DB).

Cubre el prorrateo por rendimiento, el anidado, el guard anti-ciclo y la
**paridad**: una receta plana (solo insumos) da EXACTAMENTE lo mismo que antes."""

from __future__ import annotations

import pytest

from app.domain.inventory.costing import food_cost, resolve_preparation_costs
from app.domain.inventory.exceptions import (
    InvalidQuantity,
    InvalidRecipeComponent,
    RecipeCycle,
)
from app.domain.inventory.recipe import Preparation, RecipeItem
from app.domain.shared.money import Money

ARS = "ARS"
COSTS = {"tomate": Money(1000, ARS), "carne": Money(80000, ARS)}


# --- RecipeItem: insumo XOR preparación --------------------------------------


def test_recipe_item_requires_exactly_one_component() -> None:
    RecipeItem(ingredient_id="tomate", qty=100)  # ok
    RecipeItem(preparation_id="salsa", qty=100)  # ok
    with pytest.raises(InvalidRecipeComponent):
        RecipeItem(qty=100)  # ninguno
    with pytest.raises(InvalidRecipeComponent):
        RecipeItem(ingredient_id="tomate", preparation_id="salsa", qty=100)  # ambos


def test_preparation_requires_positive_yield() -> None:
    with pytest.raises(InvalidQuantity):
        Preparation(id="p", tenant_id="t", name="Salsa", yield_qty=0)


# --- Paridad: receta plana == comportamiento anterior ------------------------


def test_flat_recipe_cost_is_unchanged() -> None:
    # Sin cost_by_preparation y solo insumos → idéntico al food cost de un nivel.
    items = [RecipeItem(ingredient_id="carne", qty=200)]  # 0.2 kg
    assert food_cost(items, COSTS, ARS) == Money(16000, ARS)  # 80000 × 0.2


# --- Preparaciones: prorrateo por rendimiento --------------------------------


def test_preparation_unit_cost_prorated_by_yield() -> None:
    # Salsa: 2.0 de tomate (a 1000/u) = 2000 la tanda; rinde 2.0 → 1000 por unidad.
    salsa = Preparation(
        id="salsa",
        tenant_id="t",
        name="Salsa fileto",
        yield_qty=2000,
        items=[RecipeItem(ingredient_id="tomate", qty=2000)],
    )
    costs = resolve_preparation_costs({"salsa": salsa}, COSTS, ARS)
    assert costs["salsa"] == Money(1000, ARS)


def test_recipe_using_preparation_and_ingredient() -> None:
    prep_costs = {"salsa": Money(1000, ARS)}
    items = [
        RecipeItem(preparation_id="salsa", qty=150),  # 0.15 × 1000 = 150
        RecipeItem(ingredient_id="carne", qty=200),  # 0.2 × 80000 = 16000
    ]
    assert food_cost(items, COSTS, ARS, cost_by_preparation=prep_costs) == Money(16150, ARS)


def test_nested_preparation_resolves_recursively() -> None:
    base = Preparation(
        id="base",
        tenant_id="t",
        name="Base",
        yield_qty=1000,
        items=[RecipeItem(ingredient_id="tomate", qty=1000)],  # 1000/u
    )
    salsa = Preparation(
        id="salsa",
        tenant_id="t",
        name="Salsa",
        yield_qty=1000,
        items=[
            RecipeItem(preparation_id="base", qty=500),  # 0.5 × 1000 = 500
            RecipeItem(ingredient_id="tomate", qty=500),  # 0.5 × 1000 = 500
        ],
    )
    costs = resolve_preparation_costs({"base": base, "salsa": salsa}, COSTS, ARS)
    assert costs["base"] == Money(1000, ARS)
    assert costs["salsa"] == Money(1000, ARS)  # batch 1000 / yield 1.0


def test_cycle_is_detected() -> None:
    a = Preparation(
        id="A", tenant_id="t", name="A", yield_qty=1000,
        items=[RecipeItem(preparation_id="B", qty=100)],
    )
    b = Preparation(
        id="B", tenant_id="t", name="B", yield_qty=1000,
        items=[RecipeItem(preparation_id="A", qty=100)],
    )
    with pytest.raises(RecipeCycle):
        resolve_preparation_costs({"A": a, "B": b}, COSTS, ARS)


def test_missing_components_contribute_zero() -> None:
    # Preparación inexistente en una receta → 0.
    assert food_cost(
        [RecipeItem(preparation_id="ghost", qty=100)], COSTS, ARS, cost_by_preparation={}
    ) == Money(0, ARS)
    # Insumo desconocido dentro de una preparación → 0.
    prep = Preparation(
        id="p", tenant_id="t", name="P", yield_qty=1000,
        items=[RecipeItem(ingredient_id="unknown", qty=1000)],
    )
    costs = resolve_preparation_costs({"p": prep}, COSTS, ARS)
    assert costs["p"] == Money(0, ARS)
