from __future__ import annotations

from app.application.public_menu.use_cases import group_menu
from app.domain.product.entities import Product
from app.domain.shared.money import Money


def _product(name: str, amount: int, category: str | None) -> Product:
    return Product(
        id=name.lower(),
        tenant_id="t1",
        name=name,
        price=Money(amount, "ARS"),
        category=category,
    )


def test_groups_by_category_preserving_first_seen_order() -> None:
    products = [
        _product("Empanada", 1500, "Entradas"),
        _product("Pizza", 12000, "Platos"),
        _product("Provoleta", 4000, "Entradas"),
    ]
    menu = group_menu(products)

    assert [c.name for c in menu] == ["Entradas", "Platos"]
    entradas = menu[0]
    assert [i.name for i in entradas.items] == ["Empanada", "Provoleta"]
    assert entradas.items[0].price_amount == 1500


def test_uncategorised_products_fall_into_a_none_group() -> None:
    menu = group_menu([_product("Agua", 800, None), _product("Gaseosa", 900, "")])
    # Both empty/None categories collapse into the single None bucket.
    assert len(menu) == 1
    assert menu[0].name is None
    assert [i.name for i in menu[0].items] == ["Agua", "Gaseosa"]


def test_empty_catalog_yields_empty_menu() -> None:
    assert group_menu([]) == []


def test_item_exposes_only_public_fields() -> None:
    [category] = group_menu([_product("Flan", 3000, "Postres")])
    item = category.items[0]
    assert item.id == "flan"
    assert item.name == "Flan"
    assert item.price_amount == 3000
    # No cost/margin/food-cost on the public DTO.
    assert not hasattr(item, "cost_amount")
