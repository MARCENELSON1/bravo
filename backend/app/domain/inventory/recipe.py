from __future__ import annotations

from dataclasses import dataclass, field

from app.domain.inventory.exceptions import InvalidQuantity


@dataclass
class RecipeItem:
    """One ingredient consumed per unit sold. ``qty`` is in milésimas of the
    ingredient's base unit (see ``QUANTITY_SCALE``)."""

    ingredient_id: str
    qty: int

    def __post_init__(self) -> None:
        if self.qty <= 0:
            raise InvalidQuantity()


@dataclass
class Recipe:
    """A product's recipe (opt-in, 1:1 with a Product), scoped to a tenant.

    A product without a recipe sells without touching stock (e.g. a bottled
    drink bought ready-made). The recipe is loaded by the OWNER/MANAGER.
    """

    product_id: str
    tenant_id: str
    items: list[RecipeItem] = field(default_factory=list)
