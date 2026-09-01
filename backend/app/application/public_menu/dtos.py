from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PublicMenuItem:
    """One sellable item on the public (customer-facing) menu. Only what a diner
    may see — never cost/food-cost/margin (those stay owner-only)."""

    id: str
    name: str
    price_amount: int


@dataclass(frozen=True)
class PublicMenuCategory:
    """A group of items under the category the owner assigned. ``name`` is ``None``
    for uncategorised products (the frontend labels that group)."""

    name: str | None
    items: list[PublicMenuItem]


@dataclass(frozen=True)
class PublicMenu:
    """The full public menu for a table's QR: the local's name + its currency/
    locale (so the frontend formats prices) + the categorised catalog."""

    tenant_name: str
    currency: str
    locale: str
    categories: list[PublicMenuCategory]


@dataclass(frozen=True)
class IssueTableQrResult:
    """The signed token + the deep link the QR encodes (``{app}/carta/{token}``)."""

    token: str
    url: str
