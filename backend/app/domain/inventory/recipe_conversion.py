"""Unit conversion for recipes (Fase 2C). Pure, integer, deterministic.

An ingredient is purchased/costed/stocked in its ``unit`` (KG or L) but a recipe
may express its quantity in the finer sub-unit of the same family (G or ML). The
conversion factor is a fixed physical constant (1000) folded into the single
``round`` of the cost line — never a per-tenant datum, so there is no DB table.
Only base→finer within a family: KG→G and L→ML. No g↔ml (needs density) and no
packs (there is no CASE unit).
"""

from __future__ import annotations

from app.domain.inventory.exceptions import IncompatibleUnits
from app.domain.inventory.value_objects import UnitOfMeasure

# Finer recipe sub-unit allowed per family (1 KG = 1000 G, 1 L = 1000 ML).
_FINER_UNIT: dict[UnitOfMeasure, UnitOfMeasure] = {
    UnitOfMeasure.KG: UnitOfMeasure.G,
    UnitOfMeasure.L: UnitOfMeasure.ML,
}
_FAMILY_FACTOR = 1000


def conversion_factor(
    base: UnitOfMeasure, recipe: UnitOfMeasure | None
) -> tuple[int, int]:
    """``(num, den)`` to convert a quantity expressed in ``recipe`` to the cost's
    ``base`` unit, folded into the cost-line rounding. Identity ``(1, 1)`` when
    there is no conversion (``recipe`` is None or equals ``base``). Only a base
    unit and its finer same-family sub-unit convert (KG→G, L→ML); anything else
    raises :class:`IncompatibleUnits`.
    """
    if recipe is None or recipe == base:
        return (1, 1)
    if _FINER_UNIT.get(base) == recipe:
        return (1, _FAMILY_FACTOR)
    raise IncompatibleUnits()


def assert_convertible(base: UnitOfMeasure, recipe: UnitOfMeasure | None) -> None:
    """Validate that ``recipe`` is an admissible recipe unit for ``base`` (None,
    the same unit, or its finer sub-unit). Raises :class:`IncompatibleUnits`."""
    conversion_factor(base, recipe)
