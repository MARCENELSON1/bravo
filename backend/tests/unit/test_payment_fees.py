"""Unit tests de comisiones: fee_of (estimada, slice A) + _mp_fee_amount (real, slice C)."""

from app.domain.payment.fees import fee_of
from app.infrastructure.payments.mercadopago_gateway import _mp_fee_amount


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


def test_mp_fee_amount_sums_details_to_minor_units():
    data = {"fee_details": [{"amount": 30.0}, {"amount": 1.5}]}
    assert _mp_fee_amount(data) == 3150  # (30 + 1.5) pesos → 3150 centavos


def test_mp_fee_amount_none_when_absent():
    assert _mp_fee_amount({}) is None
    assert _mp_fee_amount({"fee_details": []}) is None
