"""Comisión de cobro (procesador de pagos) — matemática pura, minor units enteros.

Es el eje **financiero del cobro**: lo que la pasarela (Mercado Pago / tarjeta) se
queda de cada cobro. NO confundir con el neto de IVA (2B, eje margen): son
ortogonales — la comisión vive en el ``Payment`` (``net_amount = amount − fee``), no
en ``sale_facts``.
"""

from __future__ import annotations


def fee_of(amount: int, fee_bps: int) -> int:
    """Comisión sobre un monto: ``amount × fee_bps / 10000``.

    ``fee_bps`` ≤ 0 → 0 (sin comisión cargada) → ``net == amount`` (paridad con hoy).
    """
    if fee_bps <= 0:
        return 0
    return round(amount * fee_bps / 10000)
