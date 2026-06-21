from __future__ import annotations

import pytest

from app.domain.inventory.costing import (
    food_cost,
    food_cost_ratio_bps,
    is_below_min,
    margin,
)
from app.domain.inventory.entities import Ingredient, StockMovement
from app.domain.inventory.exceptions import InvalidQuantity, InvalidUnitCost
from app.domain.inventory.recipe import RecipeItem
from app.domain.inventory.value_objects import (
    MovementDirection,
    MovementReason,
    UnitOfMeasure,
)
from app.domain.shared.exceptions import CurrencyMismatch
from app.domain.shared.money import Money


def _ingredient(stock_qty: int = 0, min_qty: int = 0, cost: int = 100) -> Ingredient:
    return Ingredient(
        id="i1",
        tenant_id="t1",
        name="Harina",
        unit=UnitOfMeasure.KG,
        stock_qty=stock_qty,
        min_qty=min_qty,
        unit_cost=Money(cost, "ARS"),
    )


def _movement(direction: MovementDirection, reason: MovementReason, qty: int) -> StockMovement:
    return StockMovement(
        id="m1",
        tenant_id="t1",
        ingredient_id="i1",
        direction=direction,
        reason=reason,
        qty=qty,
    )


def test_apply_in_increases_stock() -> None:
    ingredient = _ingredient(stock_qty=1000)
    ingredient.apply(_movement(MovementDirection.IN, MovementReason.PURCHASE, 500))
    assert ingredient.stock_qty == 1500


def test_apply_out_decreases_stock() -> None:
    ingredient = _ingredient(stock_qty=1000)
    ingredient.apply(_movement(MovementDirection.OUT, MovementReason.SALE, 300))
    assert ingredient.stock_qty == 700


def test_apply_out_can_go_negative() -> None:
    # A sale is never blocked by a shortage: stock can drop below zero.
    ingredient = _ingredient(stock_qty=200)
    ingredient.apply(_movement(MovementDirection.OUT, MovementReason.SALE, 500))
    assert ingredient.stock_qty == -300


def test_movement_rejects_non_positive_qty() -> None:
    with pytest.raises(InvalidQuantity):
        _movement(MovementDirection.IN, MovementReason.PURCHASE, 0)
    with pytest.raises(InvalidQuantity):
        _movement(MovementDirection.OUT, MovementReason.WASTE, -5)


def test_set_cost_updates_unit_cost() -> None:
    ingredient = _ingredient(cost=100)
    ingredient.set_cost(Money(250, "ARS"))
    assert ingredient.unit_cost == Money(250, "ARS")


def test_set_cost_rejects_non_positive() -> None:
    ingredient = _ingredient()
    with pytest.raises(InvalidUnitCost):
        ingredient.set_cost(Money(0, "ARS"))


def test_set_cost_rejects_currency_mismatch() -> None:
    ingredient = _ingredient()
    with pytest.raises(CurrencyMismatch):
        ingredient.set_cost(Money(250, "USD"))


def test_recipe_item_rejects_non_positive_qty() -> None:
    with pytest.raises(InvalidQuantity):
        RecipeItem(ingredient_id="i1", qty=0)


def test_is_below_min_at_or_under_limit() -> None:
    assert is_below_min(100, 100) is True  # at the limit counts as shortage
    assert is_below_min(99, 100) is True
    assert is_below_min(101, 100) is False


def test_ingredient_is_below_min_property() -> None:
    assert _ingredient(stock_qty=50, min_qty=100).is_below_min is True
    assert _ingredient(stock_qty=150, min_qty=100).is_below_min is False


def test_food_cost_sums_two_ingredients() -> None:
    # 1.5 kg flour @ 100/kg = 150 ; 0.2 kg butter @ 1000/kg = 200 → 350
    items = [
        RecipeItem(ingredient_id="flour", qty=1500),
        RecipeItem(ingredient_id="butter", qty=200),
    ]
    costs = {"flour": Money(100, "ARS"), "butter": Money(1000, "ARS")}
    assert food_cost(items, costs, "ARS") == Money(350, "ARS")


def test_food_cost_missing_ingredient_contributes_zero() -> None:
    items = [RecipeItem(ingredient_id="flour", qty=1500)]
    assert food_cost(items, {}, "ARS") == Money(0, "ARS")


def test_food_cost_empty_recipe_is_zero() -> None:
    assert food_cost([], {}, "ARS") == Money(0, "ARS")


def test_margin_can_be_negative_below_cost() -> None:
    assert margin(Money(1000, "ARS"), Money(350, "ARS")) == 650
    assert margin(Money(300, "ARS"), Money(350, "ARS")) == -50  # sold below cost


def test_food_cost_ratio_bps() -> None:
    assert food_cost_ratio_bps(Money(1000, "ARS"), Money(330, "ARS")) == 3300  # 33%
    assert food_cost_ratio_bps(Money(0, "ARS"), Money(330, "ARS")) == 0  # no price → 0
