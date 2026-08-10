from __future__ import annotations

from dataclasses import dataclass, field

from app.domain.inventory.exceptions import InvalidQuantity, InvalidRecipeComponent


@dataclass
class RecipeItem:
    """One component consumed per unit sold. Points to **either** an ingredient
    **or** a preparation (receta madre), never both. ``qty`` is in milésimas of
    that component's base unit (see ``QUANTITY_SCALE``)."""

    ingredient_id: str | None = None
    qty: int = 0
    preparation_id: str | None = None

    def __post_init__(self) -> None:
        if self.qty <= 0:
            raise InvalidQuantity()
        # Exactamente uno de insumo/preparación (XOR).
        if (self.ingredient_id is None) == (self.preparation_id is None):
            raise InvalidRecipeComponent()


@dataclass
class Recipe:
    """A product's recipe (opt-in, 1:1 with a Product), scoped to a tenant.

    A product without a recipe sells without touching stock (e.g. a bottled
    drink bought ready-made). The recipe is loaded by the OWNER/MANAGER. Its
    items may reference ingredients directly or preparations (recetas madre).
    """

    product_id: str
    tenant_id: str
    items: list[RecipeItem] = field(default_factory=list)
    # Incremental version (Fase 2D): bumped on every SetRecipe. Snapshotted into
    # sale_facts at PAID time for attribution (recipe change vs ingredient price
    # change) — the food cost itself is already frozen per sale. Default 1.
    version: int = 1


@dataclass
class Preparation:
    """A reusable base preparation (receta madre, ej. "salsa fileto"), scoped to
    a tenant. It is **not** a sellable catalog product: it only exists to be used
    by recipes (or nested inside other preparations).

    ``yield_qty`` is how much one batch yields, in milésimas of the preparation's
    own unit (ej. rinde 2.0 kg → 2000). The cost of *one* base unit is the batch
    cost prorated by the yield, so a recipe using X of it pays ``X × unit_cost``.
    """

    id: str
    tenant_id: str
    name: str
    yield_qty: int
    items: list[RecipeItem] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.yield_qty <= 0:
            raise InvalidQuantity()
