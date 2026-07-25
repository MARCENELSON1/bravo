from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select

from app.application.finance.dtos import ProductDetail, ProductSaleLine
from app.application.finance.use_cases import (
    FinanceProductDetailReadModel,
    InventoryValueReadModel,
)
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.models import IngredientORM, SaleFactORM

# Las cantidades de insumo se guardan en milésimas de la unidad base.
_QUANTITY_SCALE = 1000


class SqlAlchemyInventoryValueReadModel(InventoryValueReadModel):
    """Valor del inventario a mano: Σ (stock_qty × unit_cost) / 1000 sobre insumos
    activos (misma técnica que la valuación de mermas). Tenant-scoped; solo lectura."""

    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def total_value(self, tenant_id: str) -> int:
        async with self._session_factory() as session:
            raw = (
                await session.execute(
                    select(
                        func.coalesce(
                            func.sum(
                                IngredientORM.stock_qty * IngredientORM.unit_cost_amount
                            ),
                            0,
                        )
                    ).where(
                        IngredientORM.tenant_id == tenant_id,
                        IngredientORM.active.is_(True),
                        IngredientORM.stock_qty > 0,
                    )
                )
            ).scalar_one()
            return int(raw) // _QUANTITY_SCALE


class SqlAlchemyFinanceProductDetailReadModel(FinanceProductDetailReadModel):
    """Líneas de `sale_facts` de un producto en la ventana, con sus agregados.
    Tenant-scoped (RLS + filtro explícito); solo lectura."""

    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def detail(
        self,
        tenant_id: str,
        product_id: str,
        *,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> ProductDetail:
        async with self._session_factory() as session:
            stmt = (
                select(SaleFactORM)
                .where(
                    SaleFactORM.tenant_id == tenant_id,
                    SaleFactORM.product_id == product_id,
                )
                .order_by(SaleFactORM.occurred_at.desc())
            )
            if since is not None:
                stmt = stmt.where(SaleFactORM.occurred_at >= since)
            if until is not None:
                stmt = stmt.where(SaleFactORM.occurred_at <= until)
            rows = (await session.execute(stmt)).scalars().all()

        currency = rows[0].currency if rows else "ARS"
        lines = [
            ProductSaleLine(
                order_id=r.order_id,
                occurred_at=r.occurred_at.isoformat(),
                quantity=r.quantity,
                line_amount=r.line_amount,
                food_cost_amount=r.food_cost_amount,
                margin_amount=r.line_amount - (r.food_cost_amount or 0),
            )
            for r in rows
        ]
        return ProductDetail(
            product_id=product_id,
            currency=currency,
            units_sold=sum(r.quantity for r in rows),
            sales_amount=sum(r.line_amount for r in rows),
            food_cost_amount=sum(r.food_cost_amount or 0 for r in rows),
            margin_amount=sum(r.line_amount - (r.food_cost_amount or 0) for r in rows),
            lines=lines,
        )
