"""Pure food-cost math (no I/O): cost of a recipe, gross margin and the food
cost ratio. Integer minor units throughout (same no-float rule as Money)."""

from __future__ import annotations

from app.domain.inventory.exceptions import RecipeCycle
from app.domain.inventory.recipe import Preparation, RecipeItem
from app.domain.inventory.value_objects import FULL_YIELD_BPS, QUANTITY_SCALE
from app.domain.shared.exceptions import CurrencyMismatch
from app.domain.shared.money import Money
from app.domain.shared.vat import net_of_vat


def effective_unit_cost(unit_cost: Money, yield_pct: int) -> Money:
    """Cost per *usable* base unit: the raw unit cost adjusted for yield (merma).

    ``yield_pct`` is in basis points (10000 = 100% = no loss). A yield below 100%
    means part of the purchased ingredient is lost (bone, trim, cooking), so what
    reaches the plate costs ``raw / yield``. Same integer/round idiom as the rest
    of the costing math; the result is never below the raw cost.
    """
    # An invalid yield (0 or negative from a non-schema write) degrades to the
    # raw cost instead of dividing by zero and crashing the whole report.
    if yield_pct >= FULL_YIELD_BPS or yield_pct <= 0:
        return unit_cost
    return Money(
        round(unit_cost.amount * FULL_YIELD_BPS / yield_pct), unit_cost.currency
    )


def net_effective_unit_cost(
    unit_cost: Money, yield_pct: int, cost_includes_tax: bool, vat_bps: int
) -> Money:
    """Effective cost per usable unit (yield-adjusted), net of VAT when the loaded
    cost includes it. ``vat_bps`` 0 or ``cost_includes_tax`` False → no VAT netting
    (identity), so it stays backward compatible when VAT is unset."""
    cost = effective_unit_cost(unit_cost, yield_pct)
    if cost_includes_tax:
        return Money(net_of_vat(cost.amount, vat_bps), cost.currency)
    return cost


def food_cost(
    items: list[RecipeItem],
    cost_by_ingredient: dict[str, Money],
    currency: str,
    *,
    cost_by_preparation: dict[str, Money] | None = None,
    factor_by_ingredient: dict[str, tuple[int, int]] | None = None,
) -> Money:
    """Cost of one sold unit = Σ(recipe_qty × component unit_cost).

    Each item points to an ingredient **or** a preparation (receta madre).
    ``recipe_qty`` is in milésimas of the component's recipe unit and ``unit_cost``
    is Money per *one* base (purchase) unit, so each line is
    ``unit_cost.amount × qty × num / (den × 1000)`` (rounded to the minor unit),
    where ``(num, den)`` is the ingredient's unit-conversion factor from
    ``factor_by_ingredient`` (default identity ``(1, 1)`` → recipe unit == base
    unit). ``currency`` is required because Money always needs one — even for an
    empty recipe or when a cost is missing. A component absent from its cost map
    contributes zero (treated as unknown). Backward compatible: with no
    ``factor_by_ingredient`` (or all identity) it behaves exactly as before.
    """
    prep_costs = cost_by_preparation or {}
    factors = factor_by_ingredient or {}
    total = 0
    for item in items:
        if item.preparation_id is not None:
            cost = prep_costs.get(item.preparation_id)
            num, den = 1, 1  # a preparation carries its own unit (via yield)
        else:
            cost = cost_by_ingredient.get(item.ingredient_id)
            num, den = factors.get(item.ingredient_id, (1, 1))
        if cost is None:
            continue
        if cost.currency != currency:
            raise CurrencyMismatch()
        total += round(cost.amount * item.qty * num / (den * QUANTITY_SCALE))
    return Money(total, currency)


def resolve_preparation_costs(
    preparations: dict[str, Preparation],
    cost_by_ingredient: dict[str, Money],
    currency: str,
    *,
    factor_by_ingredient: dict[str, tuple[int, int]] | None = None,
) -> dict[str, Money]:
    """Cost of *one base unit* of each preparation, resolved multi-level.

    A preparation's batch cost is the same Σ(qty × component unit_cost) as a
    recipe, where a component may be an ingredient or a nested preparation; the
    unit cost is that batch prorated by the yield: ``batch × SCALE / yield_qty``.
    Nested preparations are resolved recursively with an anti-cycle guard
    (raises :class:`RecipeCycle` on A→…→A). Missing components contribute zero.
    Ingredient items apply their unit-conversion factor from
    ``factor_by_ingredient`` (default identity); sub-preparations do not.
    """
    resolved: dict[str, Money] = {}
    in_progress: set[str] = set()
    factors = factor_by_ingredient or {}

    def resolve(prep_id: str) -> Money:
        if prep_id in resolved:
            return resolved[prep_id]
        prep = preparations.get(prep_id)
        if prep is None:
            return Money(0, currency)  # preparación faltante → desconocida (0)
        if prep_id in in_progress:
            raise RecipeCycle()
        in_progress.add(prep_id)
        batch_total = 0
        for item in prep.items:
            if item.preparation_id is not None:
                cost = resolve(item.preparation_id)
                num, den = 1, 1
            else:
                found = cost_by_ingredient.get(item.ingredient_id)
                cost = found if found is not None else Money(0, currency)
                num, den = factors.get(item.ingredient_id, (1, 1))
            if cost.currency != currency:
                raise CurrencyMismatch()
            batch_total += round(cost.amount * item.qty * num / (den * QUANTITY_SCALE))
        in_progress.discard(prep_id)
        unit = (
            round(batch_total * QUANTITY_SCALE / prep.yield_qty)
            if prep.yield_qty > 0
            else 0
        )
        resolved[prep_id] = Money(unit, currency)
        return resolved[prep_id]

    for prep_id in preparations:
        resolve(prep_id)
    return resolved


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


def coverage_bps(confirmed: Money, total: Money) -> int:
    """Share of a plate's food cost backed by *confirmed* (purchased) ingredients,
    in basis points (10000 = 100%). ``total`` 0 → 10000 (a plate with no cost is
    trivially fully covered). Twin of :func:`food_cost_ratio_bps`."""
    if confirmed.currency != total.currency:
        raise CurrencyMismatch()
    if total.amount == 0:
        return 10000
    return round(confirmed.amount * 10000 / total.amount)


def is_below_min(stock_qty: int, min_qty: int) -> bool:
    """An ingredient is in shortage (quiebre) when at or below its minimum."""
    return stock_qty <= min_qty
