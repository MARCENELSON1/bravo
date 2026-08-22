from __future__ import annotations

from enum import StrEnum


class SessionStatus(StrEnum):
    """Estado de la sesión de mesa. En vivo es DERIVADO de los ítems de sus comandas
    (ver el read model del floor); el valor almacenado es un cache que se sella en
    las transiciones clave (a_cobrar/cerrada). `libre` = no hay sesión → no se
    almacena."""

    OPEN = "OPEN"  # abierta, sin ítems marchados
    IN_KITCHEN = "IN_KITCHEN"  # en_cocina
    TO_SERVE = "TO_SERVE"  # para_servir (máxima prioridad)
    SERVED = "SERVED"  # servida
    TO_CHARGE = "TO_CHARGE"  # a_cobrar
    CLOSED = "CLOSED"  # cerrada


class SessionOrigin(StrEnum):
    """De dónde viene la venta de la sesión. SALON por default (paridad)."""

    SALON = "SALON"
    MOSTRADOR = "MOSTRADOR"
    DELIVERY = "DELIVERY"
    TAKEAWAY = "TAKEAWAY"
