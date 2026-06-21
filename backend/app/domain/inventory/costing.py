"""Pure food-cost math (no I/O): cost of a recipe, gross margin and the food
cost ratio. Integer minor units throughout (same no-float rule as Money)."""

from __future__ import annotations

from app.domain.inventory.recipe import RecipeItem
from app.domain.inventory.value_objects import QUANTITY_SCALE
from app.domain.shared.exceptions import CurrencyMismatch
from app.domain.shared.money import Money


def food_cost(
    items: list[RecipeItem],
    cost_by_ingredient: dict[str, Money],
    currency: str,
) -> Money:
    """Cost of one sold unit = Σ(recipe_qty × ingredient unit_cost).

    ``recipe_qty`` is in milésimas of the base unit and ``unit_cost`` is Money
    per *one* base unit, so each line is ``unit_cost.amount × qty / 1000``
    (rounded to the minor unit). ``currency`` is required because Money always
    needs one — even for an empty recipe or when a cost is missing. An ingredient
    absent from ``cost_by_ingredient`` contributes zero (treated as unknown).
    """
    total = 0
    for item in items:
        cost = cost_by_ingredient.get(item.ingredient_id)
        if cost is None:
            continue
        if cost.currency != currency:
            raise CurrencyMismatch()
        total += round(cost.amount * item.qty / QUANTITY_SCALE)
    return Money(total, currency)


def margin(price: Money, food_cost: Money) -> int:
    """Gross margin in minor units (price − food cost).

    Returns a plain ``int`` (not Money) because it may be **negative** when a
    product is sold below cost — a food-cost tool must surface the loss, not
    hide it, and Money cannot hold a negative amount.
    """
    if price.currency != food_cost.currency:
        raise CurrencyMismatch()
    return price.amount - food_cost.amount


def food_cost_ratio_bps(price: Money, food_cost: Money) -> int:
    """Food cost as a fraction of price, in basis points (e.g. 3300 = 33%).

    Zero when the price is zero (avoids division by zero); can exceed 10000
    when the product is sold below cost.
    """
    if price.currency != food_cost.currency:
        raise CurrencyMismatch()
    if price.amount == 0:
        return 0
    return round(food_cost.amount * 10000 / price.amount)


def is_below_min(stock_qty: int, min_qty: int) -> bool:
    """An ingredient is in shortage (quiebre) when at or below its minimum."""
    return stock_qty <= min_qty
