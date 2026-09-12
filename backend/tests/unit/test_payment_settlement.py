"""La cuenta de "cuánto se pagó" y "cuánto se puede cobrar todavía".

Estaba escrita cuatro veces con la misma forma copiada, y la diferencia entre las
dos preguntas —lo cobrado no descuenta lo que alguien está pagando ahora— es lo
que permitía que dos comensales dividiendo la cuenta la pagaran entera cada uno.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.domain.payment.entities import Payment
from app.domain.payment.settlement import (
    RESERVATION_WINDOW,
    available_to_charge,
    outstanding_amount,
    reserved_amount,
    settled_amount,
)
from app.domain.payment.value_objects import PaymentDirection, PaymentMethod, PaymentStatus
from app.domain.shared.money import Money

_NOW = datetime(2026, 9, 8, 12, 0, tzinfo=UTC)


def _pay(
    amount: int,
    status: PaymentStatus = PaymentStatus.CONFIRMED,
    *,
    direction: PaymentDirection = PaymentDirection.INFLOW,
    age: timedelta = timedelta(0),
) -> Payment:
    return Payment(
        id=f"p{amount}{status.value}{age}",
        tenant_id="t1",
        direction=direction,
        amount=Money(amount, "ARS"),
        method=PaymentMethod.CASH,
        status=status,
        order_id="o1",
        created_at=_NOW - age,
    )


class TestSettled:
    def test_solo_cuenta_entradas_confirmadas(self) -> None:
        payments = [
            _pay(1000),
            _pay(500, PaymentStatus.PENDING),
            _pay(300, PaymentStatus.FAILED),
            _pay(700, direction=PaymentDirection.OUTFLOW),
        ]
        assert settled_amount(payments) == 1000

    def test_un_reembolso_deja_de_contar_solo(self) -> None:
        """Reembolsar NO crea un movimiento saliente: pasa el cobro a REFUNDED.

        Por eso el saldo se reabre sin restar nada — y por eso no hace falta
        "netear entradas menos salidas", que sobre una comanda no existen.
        """
        assert settled_amount([_pay(1000), _pay(400, PaymentStatus.REFUNDED)]) == 1000


class TestReserved:
    def test_un_cobro_en_curso_reserva(self) -> None:
        assert reserved_amount([_pay(800, PaymentStatus.PENDING)], now=_NOW) == 800

    def test_un_cobro_abandonado_libera_al_vencer(self) -> None:
        """Si no venciera, un checkout que nadie terminó trabaría la mesa para siempre."""
        viejo = _pay(800, PaymentStatus.PENDING, age=RESERVATION_WINDOW + timedelta(seconds=1))
        assert reserved_amount([viejo], now=_NOW) == 0

    def test_lo_confirmado_no_reserva_dos_veces(self) -> None:
        """Un cobro confirmado ya está en `settled`; contarlo también acá lo duplicaría."""
        assert reserved_amount([_pay(1000)], now=_NOW) == 0

    def test_sin_fecha_se_cuenta_vigente(self) -> None:
        """Trabar de más se destraba solo; dejar pasar un doble cobro hay que devolverlo."""
        sin_fecha = Payment(
            id="p",
            tenant_id="t1",
            direction=PaymentDirection.INFLOW,
            amount=Money(500, "ARS"),
            method=PaymentMethod.CASH,
            status=PaymentStatus.PENDING,
            order_id="o1",
        )
        assert reserved_amount([sin_fecha], now=_NOW) == 500


class TestOutstanding:
    def test_expone_el_excedente_en_vez_de_esconderlo(self) -> None:
        """El bug de H2: con piso en cero, cobrar de más se veía igual que saldar."""
        assert outstanding_amount(20000, [_pay(20000), _pay(20000)]) == -20000


class TestAvailable:
    def test_descuenta_lo_reservado(self) -> None:
        """El caso exacto del hallazgo: mesa de $20.000, alguien ya está pagando el total.

        Antes esto devolvía 20000 y el segundo comensal podía crear su cobro.
        """
        en_curso = [_pay(20000, PaymentStatus.PENDING)]
        assert available_to_charge(20000, en_curso, now=_NOW) == 0

    def test_la_cuenta_dividida_sigue_funcionando(self) -> None:
        """Reservar no puede romper el caso normal: uno paga su mitad, el otro la suya."""
        mitad_en_curso = [_pay(10000, PaymentStatus.PENDING)]
        assert available_to_charge(20000, mitad_en_curso, now=_NOW) == 10000

    def test_nunca_negativo(self) -> None:
        """Como tope de un cobro nuevo, cero significa "no cobres más"."""
        assert available_to_charge(20000, [_pay(20000), _pay(20000)], now=_NOW) == 0

    def test_sin_cobros_es_el_total(self) -> None:
        assert available_to_charge(20000, [], now=_NOW) == 20000
