from __future__ import annotations

import pytest

from app.domain.product.exceptions import (
    InvalidModifierGroup,
    InvalidModifierSelection,
)
from app.domain.product.modifiers import ModifierGroup, ModifierOption, select_options

_DEFAULT = object()


def _group(gid="g1", *, min_select=0, max_select=1, options=_DEFAULT) -> ModifierGroup:
    if options is _DEFAULT:
        options = [ModifierOption(id="o1", name="A"), ModifierOption(id="o2", name="B")]
    return ModifierGroup(
        id=gid,
        tenant_id="t1",
        product_id="p1",
        name="Grupo",
        min_select=min_select,
        max_select=max_select,
        options=options,
    )


def test_option_rejects_blank_name_and_negative_delta() -> None:
    with pytest.raises(InvalidModifierGroup):
        ModifierOption(id="o", name="  ")
    with pytest.raises(InvalidModifierGroup):
        ModifierOption(id="o", name="X", price_delta=-1)


def test_group_rejects_bad_rules() -> None:
    with pytest.raises(InvalidModifierGroup):
        _group(options=[])  # sin opciones
    with pytest.raises(InvalidModifierGroup):
        _group(min_select=2, max_select=1)  # max < min
    with pytest.raises(InvalidModifierGroup):
        _group(min_select=3)  # exige más de las opciones que hay (2)


def test_required_is_derived_from_min_select() -> None:
    assert _group(min_select=1).required is True
    assert _group(min_select=0).required is False


def test_select_options_happy_path_snapshots_price() -> None:
    group = _group(
        min_select=1,
        max_select=1,
        options=[
            ModifierOption(id="rare", name="Jugosa", price_delta=0),
            ModifierOption(id="bacon", name="Panceta", price_delta=1200),
        ],
    )
    chosen = select_options([group], ["bacon"])
    assert [(o.id, o.price_delta) for o in chosen] == [("bacon", 1200)]


def test_select_options_enforces_min() -> None:
    group = _group(min_select=1, max_select=2)
    with pytest.raises(InvalidModifierSelection):
        select_options([group], [])  # requerido, no eligió


def test_select_options_enforces_max() -> None:
    group = _group(min_select=0, max_select=1)
    with pytest.raises(InvalidModifierSelection):
        select_options([group], ["o1", "o2"])  # eligió 2, el máximo es 1


def test_select_options_rejects_unknown_option() -> None:
    with pytest.raises(InvalidModifierSelection):
        select_options([_group()], ["nope"])


def test_no_groups_and_no_selection_is_ok() -> None:
    assert select_options([], []) == []
