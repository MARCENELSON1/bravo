"""Shared SQL column expressions over ``sale_facts`` (Solución 1).

Single source of truth for the frozen net-of-VAT columns with their fallback to
gross for rows written before the migration (``line_net_amount`` /
``food_cost_net_amount`` are nullable). Reused by every read model that sums the
net sales / net food so the fallback semantics can't drift between screens.
"""

from __future__ import annotations

from sqlalchemy import func

from app.infrastructure.persistence.models import SaleFactORM


def net_sales_col():
    """Ventas netas de IVA congeladas; filas previas a la migración caen al bruto."""
    return func.coalesce(SaleFactORM.line_net_amount, SaleFactORM.line_amount, 0)


def net_food_col():
    """Food cost neto congelado; filas previas a la migración caen al bruto."""
    return func.coalesce(
        SaleFactORM.food_cost_net_amount, SaleFactORM.food_cost_amount, 0
    )
