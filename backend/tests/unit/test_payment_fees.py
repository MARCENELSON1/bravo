"""Unit tests para la comisión de cobro (comisiones slice A): fee_of puro."""

from app.domain.payment.fees import fee_of


def test_fee_of_zero_or_negative_rate_is_zero():
    # Sin tasa cargada → 0 → net == amount (paridad).
    assert fee_of(100000, 0) == 0
    assert fee_of(100000, -5) == 0


def test_fee_of_computes_percentage():
    assert fee_of(100000, 300) == 3000  # 3%
    assert fee_of(1000, 300) == 30
    assert fee_of(200000, 600) == 12000  # 6%


def test_fee_of_rounds_to_nearest_cent():
    assert fee_of(333, 300) == 10  # 9.99 → 10
