from __future__ import annotations

from dataclasses import dataclass, field

from app.domain.product.exceptions import (
    InvalidModifierGroup,
    InvalidModifierSelection,
)


@dataclass
class ModifierOption:
    """One choice inside a modifier group (ej. "+Panceta", "Bien cocida"). Its
    ``price_delta`` (minor units, ≥ 0) adds to the plate's price when chosen — a
    plain option (ej. "sin cebolla") is just a delta of 0."""

    id: str
    name: str
    price_delta: int = 0

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise InvalidModifierGroup()
        if self.price_delta < 0:
            raise InvalidModifierGroup()


@dataclass
class ModifierGroup:
    """A group of options the diner picks from for a product (ej. "Punto de
    cocción", "Agregados"), scoped to a tenant. ``min_select``/``max_select`` are
    the rules: ``min 1, max 1`` = pick exactly one (required single-choice);
    ``min 0, max 3`` = up to three extras (optional). "Required" is derived as
    ``min_select >= 1``. Simple groups only — no nested/conditional rules."""

    id: str
    tenant_id: str
    product_id: str
    name: str
    min_select: int = 0
    max_select: int = 1
    options: list[ModifierOption] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise InvalidModifierGroup()
        if not self.options:
            raise InvalidModifierGroup()
        if self.min_select < 0 or self.max_select < 1:
            raise InvalidModifierGroup()
        if self.max_select < self.min_select:
            raise InvalidModifierGroup()
        # Can't require choosing more distinct options than the group offers.
        if self.min_select > len(self.options):
            raise InvalidModifierGroup()

    @property
    def required(self) -> bool:
        return self.min_select >= 1


def select_options(
    groups: list[ModifierGroup], selected_option_ids: list[str]
) -> list[ModifierOption]:
    """Resolve a diner's chosen option ids against a product's modifier groups,
    enforcing each group's min/max. Pure — no I/O. Returns the chosen options (in
    the order they were sent) so the caller can snapshot name + price_delta onto
    the order line. Prices come from these options, never from the client.

    Raises ``InvalidModifierSelection`` if an id is unknown to the product or a
    group's min/max is violated (too few required, or too many)."""
    option_by_id: dict[str, ModifierOption] = {}
    group_of_option: dict[str, str] = {}
    for group in groups:
        for option in group.options:
            option_by_id[option.id] = option
            group_of_option[option.id] = group.id

    chosen: list[ModifierOption] = []
    count_by_group: dict[str, int] = {}
    for option_id in selected_option_ids:
        option = option_by_id.get(option_id)
        if option is None:
            raise InvalidModifierSelection()
        chosen.append(option)
        gid = group_of_option[option_id]
        count_by_group[gid] = count_by_group.get(gid, 0) + 1

    for group in groups:
        count = count_by_group.get(group.id, 0)
        if count < group.min_select or count > group.max_select:
            raise InvalidModifierSelection()

    return chosen
