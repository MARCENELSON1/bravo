"""Unit: lectura tolerante de la unidad de insumo (no romper con datos legacy)."""

from __future__ import annotations

import pytest

from app.domain.inventory.value_objects import UnitOfMeasure


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("KG", UnitOfMeasure.KG),
        ("kg", UnitOfMeasure.KG),  # case-insensitive
        (" G ", UnitOfMeasure.G),  # trim
        ("kilo", UnitOfMeasure.KG),  # alias ES
        ("gramos", UnitOfMeasure.G),
        ("litro", UnitOfMeasure.L),
        ("cc", UnitOfMeasure.ML),
        ("unidad", UnitOfMeasure.UNIT),
        # Los que rompían el food cost: legacy inválidas → UNIT (neutro), sin 500.
        ("dosis", UnitOfMeasure.UNIT),
        ("porción", UnitOfMeasure.UNIT),
        ("cualquier cosa", UnitOfMeasure.UNIT),
        ("", UnitOfMeasure.UNIT),
    ],
)
def test_parse_is_tolerant(raw: str, expected: UnitOfMeasure) -> None:
    assert UnitOfMeasure.parse(raw) is expected


def test_strict_constructor_still_rejects_bad_units() -> None:
    # Los writes (create/update) usan el constructor estricto → siguen rechazando.
    with pytest.raises(ValueError):
        UnitOfMeasure("dosis")
