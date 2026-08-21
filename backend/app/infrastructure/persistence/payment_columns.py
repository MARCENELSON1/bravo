"""Helper SQL compartido para el neto financiero de cobro (comisiones). Espejo de
``sale_fact_columns.py`` (netos de IVA). Mantiene el COALESCE en un solo lugar para
que todos los read models (Home, Finanzas, payment-mix) coincidan."""

from __future__ import annotations

from sqlalchemy import func

from app.infrastructure.persistence.models import PaymentORM


def net_collected_col():  # type: ignore[no-untyped-def]
    """Neto financiero cobrado: ``net_amount`` si está, si no ``amount`` (paridad
    para pagos previos / sin comisión cargada)."""
    return func.coalesce(PaymentORM.net_amount, PaymentORM.amount, 0)
