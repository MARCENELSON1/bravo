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


def test_mp_fee_amount_no_arrastra_error_de_punto_flotante():
    """El adapter era el único lugar donde la plata pasaba por float.

    ``0.1 + 0.2`` da ``0.30000000000000004``: sumando en float y redondeando al
    final, una comisión partida en varios ``fee_details`` puede caer un centavo
    del lado equivocado. Convertir cada parte con Decimal lo hace exacto.
    """
    data = {"fee_details": [{"amount": 0.1}, {"amount": 0.2}]}
    assert _mp_fee_amount(data) == 30  # 0.30 pesos → 30 centavos, sin residuo

    # Un caso con muchas partes: el error de float se acumula, el de Decimal no.
    muchas = {"fee_details": [{"amount": 0.07} for _ in range(10)]}
    assert _mp_fee_amount(muchas) == 70  # 10 × 0,07 = 0,70


def test_mp_fee_amount_redondea_medio_centavo_hacia_arriba():
    assert _mp_fee_amount({"fee_details": [{"amount": 1.005}]}) == 101


class TestComisionSobreLaPropina:
    """La estimación tiene que medir lo mismo que después cobra la pasarela.

    La propina viaja como un ítem más del mismo cobro, así que MP cobra comisión
    sobre venta + propina. Estimar solo sobre la venta subestimaba el costo en
    exactamente ``tasa × propina``, siempre para el mismo lado.
    """

    def test_la_base_incluye_la_propina(self):
        # Venta 10.000 + propina 1.000, tasa 3,5% → 385, no 350.
        assert fee_of(1000000 + 100000, 350) == 38500

    def test_la_diferencia_es_exactamente_tasa_por_propina(self):
        venta, propina, tasa = 1000000, 100000, 350
        assert fee_of(venta + propina, tasa) - fee_of(venta, tasa) == fee_of(propina, tasa)

    def test_sin_propina_no_cambia_nada(self):
        """Paridad: el cobro sin propina —la mayoría— da idéntico que antes."""
        assert fee_of(1000000 + 0, 350) == fee_of(1000000, 350)
