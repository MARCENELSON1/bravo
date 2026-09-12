from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class PublicMenuModifierOption:
    """A choice inside a public menu item's modifier group (id + display + delta)."""

    id: str
    name: str
    price_delta: int


@dataclass(frozen=True)
class PublicMenuModifierGroup:
    """A modifier group as the diner sees it: the rules (min/max/required) + its
    options. ``required`` is derived from ``min_select``."""

    id: str
    name: str
    min_select: int
    max_select: int
    required: bool
    options: list[PublicMenuModifierOption]


@dataclass(frozen=True)
class PublicMenuItem:
    """One sellable item on the public (customer-facing) menu. Only what a diner
    may see — never cost/food-cost/margin (those stay owner-only)."""

    id: str
    name: str
    price_amount: int
    image_url: str | None = None
    description: str | None = None
    available_today: bool = True
    modifier_groups: list[PublicMenuModifierGroup] = field(default_factory=list)


@dataclass(frozen=True)
class PublicMenuCategory:
    """A group of items under the category the owner assigned. ``name`` is ``None``
    for uncategorised products (the frontend labels that group)."""

    name: str | None
    items: list[PublicMenuItem]


@dataclass(frozen=True)
class PublicMenu:
    """The full public menu for a table's QR: the local's name + its currency/
    locale (so the frontend formats prices) + the categorised catalog. The
    self-order flags tell the carta whether to show the cart at all and whether a
    submitted order waits for the waiter's confirmation (the kitchen gate)."""

    tenant_name: str
    currency: str
    locale: str
    categories: list[PublicMenuCategory]
    self_order_enabled: bool = False
    self_order_requires_confirmation: bool = True


@dataclass(frozen=True)
class IssueTableQrResult:
    """The signed token + the deep link the QR encodes (``{app}/carta/{token}``)."""

    token: str
    url: str
