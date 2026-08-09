"""Unit tests for merma (yield_pct): the effective cost per usable unit and
its parity with the flat cost when yield is 100%."""

from __future__ import annotations

from app.domain.inventory.costing import effective_unit_cost, food_cost
from app.domain.inventory.recipe import RecipeItem
from app.domain.shared.money import Money

ARS = "ARS"


def test_full_yield_is_identity() -> None:
    cost = Money(1000, ARS)
    assert effective_unit_cost(cost, 10000) == cost


def test_invalid_yield_degrades_to_raw_cost() -> None:
    # An out-of-band 0/negative yield must not divide by zero — it degrades to raw.
    cost = Money(1000, ARS)
    assert effective_unit_cost(cost, 0) == cost
    assert effective_unit_cost(cost, -5) == cost


def test_yield_below_100_raises_effective_cost() -> None:
    # 80% yield → effective cost 1000 / 0.8 = 1250.
    assert effective_unit_cost(Money(1000, ARS), 8000) == Money(1250, ARS)


def test_half_yield_doubles_cost() -> None:
    assert effective_unit_cost(Money(500, ARS), 5000) == Money(1000, ARS)


def test_food_cost_unchanged_when_yield_is_full() -> None:
    # Parity: with effective cost == raw (100% yield), the food cost is unchanged.
    items = [RecipeItem(ingredient_id="carne", qty=200)]
    costs = {"carne": effective_unit_cost(Money(1000, ARS), 10000)}
    assert food_cost(items, costs, ARS) == Money(200, ARS)


def test_food_cost_reflects_merma() -> None:
    # 0.2 of meat at effective cost 1250 (80% yield) → food cost 250.
    items = [RecipeItem(ingredient_id="carne", qty=200)]
    costs = {"carne": effective_unit_cost(Money(1000, ARS), 8000)}
    assert food_cost(items, costs, ARS) == Money(250, ARS)
