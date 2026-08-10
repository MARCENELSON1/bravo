"""Unit tests for cost coverage (Fase 3): the pure coverage_bps ratio."""

from __future__ import annotations

import pytest

from app.domain.inventory.costing import coverage_bps
from app.domain.shared.exceptions import CurrencyMismatch
from app.domain.shared.money import Money


def test_coverage_full_when_all_confirmed() -> None:
    assert coverage_bps(Money(1000, "ARS"), Money(1000, "ARS")) == 10000


def test_coverage_partial() -> None:
    assert coverage_bps(Money(500, "ARS"), Money(1000, "ARS")) == 5000
    assert coverage_bps(Money(0, "ARS"), Money(1000, "ARS")) == 0


def test_coverage_zero_total_is_fully_covered() -> None:
    # Un plato sin costo (receta vacía / sin insumos) está trivialmente cubierto.
    assert coverage_bps(Money(0, "ARS"), Money(0, "ARS")) == 10000


def test_coverage_currency_mismatch() -> None:
    with pytest.raises(CurrencyMismatch):
        coverage_bps(Money(500, "ARS"), Money(1000, "USD"))
