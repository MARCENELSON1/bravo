"""Unit tests for recipe unit conversion (Fase 2C): the family factor, its
validation, and that the cost engine stays byte-for-byte identical when no
conversion is set (parity) while converting exactly when it is."""

from __future__ import annotations

import pytest

from app.domain.inventory.costing import food_cost
from app.domain.inventory.exceptions import IncompatibleUnits
from app.domain.inventory.recipe import RecipeItem
from app.domain.inventory.recipe_conversion import assert_convertible, conversion_factor
from app.domain.inventory.value_objects import UnitOfMeasure as U
from app.domain.shared.money import Money


def test_conversion_factor_identity_and_family() -> None:
    assert conversion_factor(U.KG, None) == (1, 1)
    assert conversion_factor(U.KG, U.KG) == (1, 1)
    assert conversion_factor(U.KG, U.G) == (1, 1000)
    assert conversion_factor(U.L, U.ML) == (1, 1000)
    assert conversion_factor(U.UNIT, None) == (1, 1)


def test_conversion_factor_rejects_incompatible() -> None:
    for base, recipe in [
        (U.G, U.KG),  # fina → grande, no soportado
        (U.KG, U.ML),  # masa ↔ volumen
        (U.G, U.ML),
        (U.UNIT, U.G),
        (U.ML, U.L),
    ]:
        with pytest.raises(IncompatibleUnits):
            conversion_factor(base, recipe)


def test_assert_convertible_ok_and_raises() -> None:
    assert_convertible(U.KG, U.G)  # no lanza
    assert_convertible(U.L, None)
    assert_convertible(U.KG, U.KG)
    with pytest.raises(IncompatibleUnits):
        assert_convertible(U.KG, U.ML)


def test_food_cost_identity_without_factor_is_unchanged() -> None:
    # Paridad: sin factor == factor identidad == comportamiento actual.
    items = [RecipeItem(ingredient_id="carne", qty=200)]  # 0,2 unidad base
    costs = {"carne": Money(1000, "ARS")}  # 1000 por unidad base
    baseline = food_cost(items, costs, "ARS")
    assert baseline == Money(200, "ARS")  # 1000 * 200 / 1000
    assert (
        food_cost(items, costs, "ARS", factor_by_ingredient={"carne": (1, 1)}) == baseline
    )
    assert food_cost(items, costs, "ARS", factor_by_ingredient=None) == baseline


def test_food_cost_with_kg_to_g_conversion_is_exact() -> None:
    # aceite ARS 15,50/kg (1550 c), receta 300 g → 1550*300000/(1000*1000) = 465 c
    items = [RecipeItem(ingredient_id="aceite", qty=300_000)]  # 300 g en milésimas
    costs = {"aceite": Money(1550, "ARS")}  # por kg
    fc = food_cost(
        items, costs, "ARS", factor_by_ingredient={"aceite": conversion_factor(U.KG, U.G)}
    )
    assert fc == Money(465, "ARS")


def test_food_cost_pinch_keeps_precision() -> None:
    # insumo ARS 5000/kg (500000 c), pizca 0,5 g (500 milésimas) →
    # 500000*500/(1000*1000) = 250 c (con milésimas de kg habría redondeado a 0).
    items = [RecipeItem(ingredient_id="azafran", qty=500)]
    costs = {"azafran": Money(500_000, "ARS")}
    fc = food_cost(items, costs, "ARS", factor_by_ingredient={"azafran": (1, 1000)})
    assert fc == Money(250, "ARS")
