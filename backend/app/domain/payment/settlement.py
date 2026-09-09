"""Cuánto se pagó de una comanda y cuánto se puede todavía cobrar.

Esta cuenta estaba escrita cuatro veces —el saldo que ve el comensal, el que
elige qué comanda cobrar, el que salda la orden y el que libera la mesa— con la
misma forma copiada. Vive acá una sola vez porque las cuatro tienen que dar lo
mismo: que difieran es exactamente cómo se cobra dos veces lo mismo.

**Dos preguntas distintas, dos funciones.** "¿Cuánto entró?" solo puede contar
plata confirmada — un checkout abierto no salda nada. "¿Cuánto se puede cobrar
todavía?" además tiene que descontar los cobros en curso, o dos comensales
dividiendo la cuenta ven el total completo cada uno y la pagan entera los dos.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from app.domain.payment.entities import Payment
from app.domain.payment.value_objects import PaymentDirection, PaymentStatus

# Cuánto vale una reserva. Es el tiempo que alguien puede tener el checkout de la
# pasarela abierto sin que su parte se libere. Corto de más deja pasar el doble
# cobro que esto viene a evitar; largo de más traba la mesa cuando el comensal
# abandona el pago y nadie lo cancela. Diez minutos es holgado para pagar con el
# celular y acotado para que un abandono no moleste al resto.
RESERVATION_WINDOW = timedelta(minutes=10)


def settled_amount(payments: list[Payment]) -> int:
    """Lo efectivamente cobrado de una comanda.

    Solo entradas **confirmadas**. Un reembolso no aparece como movimiento
    saliente: cambia el estado del cobro original a ``REFUNDED``, así que deja de
    contar acá solo y el saldo se reabre sin necesidad de restar nada.
    """
    return sum(
        p.amount.amount
        for p in payments
        if p.direction is PaymentDirection.INFLOW and p.status is PaymentStatus.CONFIRMED
    )


def reserved_amount(payments: list[Payment], *, now: datetime) -> int:
    """Lo que hay comprometido en cobros iniciados y todavía sin resolver.

    Un cobro sin ``created_at`` (nunca debería pasar: la columna la llena la DB)
    se cuenta como vigente. Preferimos trabar un cobro de más antes que dejar
    pasar uno doble: lo primero se destraba solo en diez minutos, lo segundo hay
    que devolverlo.
    """
    return sum(
        p.amount.amount
        for p in payments
        if p.direction is PaymentDirection.INFLOW
        and p.status is PaymentStatus.PENDING
        and (p.created_at is None or now - p.created_at < RESERVATION_WINDOW)
    )


def outstanding_amount(total: int, payments: list[Payment]) -> int:
    """Lo que la comanda todavía debe. **Puede ser negativo**: si entró de más,
    ese excedente es plata a devolver y tiene que verse, no esconderse en cero."""
    return total - settled_amount(payments)


def available_to_charge(total: int, payments: list[Payment], *, now: datetime) -> int:
    """Lo máximo que se puede cobrar ahora mismo, descontando lo ya cobrado **y lo
    reservado**. Nunca negativo: como tope de un cobro nuevo, cero significa "no
    cobres nada más"."""
    return max(outstanding_amount(total, payments) - reserved_amount(payments, now=now), 0)
