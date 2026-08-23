"""Unit: promedio ponderado (PPP) del costo de un insumo al comprar."""

from __future__ import annotations

from app.domain.inventory.costing import weighted_unit_cost
from app.domain.shared.money import Money


def test_ppp_blends_by_quantity():
    # 50 kg (50000 milésimas) a $800 + 1 kg a $2000 → $823.5/kg → 824 (round).
    new = weighted_unit_cost(50_000, Money(800, "ARS"), 1_000, Money(2000, "ARS"))
    assert new == Money(824, "ARS")


def test_ppp_moves_gently_not_a_jump():
    # El costo NO salta al precio caro: queda muchísimo más cerca del viejo.
    new = weighted_unit_cost(50_000, Money(800, "ARS"), 1_000, Money(2000, "ARS"))
    assert 800 < new.amount < 900


def test_no_prior_stock_falls_back_to_purchase_price():
    # Sin stock previo el promedio no tiene sentido → precio de compra (last-cost).
    new = weighted_unit_cost(0, Money(500, "ARS"), 2_000, Money(1200, "ARS"))
    assert new == Money(1200, "ARS")


def test_negative_stock_falls_back_to_purchase_price():
    new = weighted_unit_cost(-3_000, Money(500, "ARS"), 2_000, Money(1200, "ARS"))
    assert new == Money(1200, "ARS")


def test_same_price_keeps_cost():
    new = weighted_unit_cost(10_000, Money(1000, "ARS"), 5_000, Money(1000, "ARS"))
    assert new == Money(1000, "ARS")
