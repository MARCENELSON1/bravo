from __future__ import annotations

from sqlalchemy import func, select

from app.application.inventory.use_cases import (
    SupplierPurchases,
    SupplierPurchasesReadModel,
)
from app.domain.inventory.value_objects import QUANTITY_SCALE, MovementReason
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.models import StockMovementORM, TenantORM


class SqlAlchemySupplierPurchasesReadModel(SupplierPurchasesReadModel):
    """Σ (qty × unit_cost) / 1000 + conteo + última, sobre movimientos PURCHASE
    con ese proveedor. Tenant-scoped; solo lectura."""

    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def summary(self, tenant_id: str, supplier_id: str) -> SupplierPurchases:
        async with self._session_factory() as db:
            currency = (
                await db.execute(
                    select(TenantORM.currency).where(TenantORM.id == tenant_id)
                )
            ).scalar_one_or_none() or "ARS"

            total_qcost, count, last = (
                await db.execute(
                    select(
                        func.coalesce(
                            func.sum(
                                StockMovementORM.qty
                                * StockMovementORM.unit_cost_amount
                            ),
                            0,
                        ),
                        func.count(),
                        func.max(StockMovementORM.created_at),
                    ).where(
                        StockMovementORM.tenant_id == tenant_id,
                        StockMovementORM.supplier_id == supplier_id,
                        StockMovementORM.reason == MovementReason.PURCHASE.value,
                    )
                )
            ).one()

        return SupplierPurchases(
            supplier_id=supplier_id,
            currency=currency,
            # qty va en milésimas → dividir por la escala para pesos reales.
            total_spent=int(total_qcost) // QUANTITY_SCALE,
            purchase_count=int(count),
            last_purchase_at=last,
        )
