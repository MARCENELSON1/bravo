from __future__ import annotations

from enum import StrEnum

# Quantities are integers in thousandths (milésimas) of the ingredient's base
# unit — same no-float rule as Money. So 1500 means 1.5 of the base unit
# (e.g. 1.5 kg if the unit is KG). Costs are Money per *one* base unit.
QUANTITY_SCALE = 1000

# Ingredient yield (rendimiento / merma) in basis points: 10000 = 100% = no loss.
# What reaches the plate costs raw_cost / (yield / 10000): a lower yield (bone,
# trim, cooking loss) raises the effective cost of the usable ingredient.
FULL_YIELD_BPS = 10000


class UnitOfMeasure(StrEnum):
    """Base unit an ingredient (insumo) is measured in. No automatic conversion
    between units (kg↔g deferred): stock, recipe and purchase all share the
    ingredient's own base unit."""

    G = "G"
    KG = "KG"
    ML = "ML"
    L = "L"
    UNIT = "UNIT"


class MovementDirection(StrEnum):
    """Whether a stock movement adds to (IN) or removes from (OUT) stock."""

    IN = "IN"
    OUT = "OUT"


class MovementReason(StrEnum):
    """Why stock moved (for audit). PURCHASE/SALE/WASTE/ADJUSTMENT."""

    PURCHASE = "PURCHASE"  # IN — restock, updates unit_cost
    SALE = "SALE"  # OUT — consumed by an order's recipe
    WASTE = "WASTE"  # OUT — merma registered by hand
    ADJUSTMENT = "ADJUSTMENT"  # IN/OUT — manual correction
