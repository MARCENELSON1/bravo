from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import func, select

from app.application.product.dtos import (
    PriceChange,
    ProductPricingBase,
    ProductRotation,
    WeekdayRotationRow,
)
from app.application.product.use_cases import (
    PriceChangeRepository,
    PricingReadModel,
    RotationReadModel,
)
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.models import (
    ProductORM,
    ProductPriceChangeORM,
    SaleFactORM,
    TenantORM,
)


async def _tenant_currency(session, tenant_id: str) -> str:
    return (
        await session.execute(select(TenantORM.currency).where(TenantORM.id == tenant_id))
    ).scalar_one_or_none() or "ARS"


class SqlAlchemyPriceChangeRepository(PriceChangeRepository):
    """Write + read del log de precios. Scoped por ``tenant_id`` (RLS + filtro)."""

    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def record(
        self,
        *,
        tenant_id: str,
        product_id: str,
        old_price_amount: int | None,
        new_price_amount: int,
        currency: str,
    ) -> None:
        async with self._session_factory() as session:
            session.add(
                ProductPriceChangeORM(
                    id=str(uuid4()),
                    tenant_id=tenant_id,
                    product_id=product_id,
                    old_price_amount=old_price_amount,
                    new_price_amount=new_price_amount,
                    currency=currency,
                )
            )

    async def list_for_product(
        self, tenant_id: str, product_id: str
    ) -> list[PriceChange]:
        async with self._session_factory() as session:
            stmt = (
                select(ProductPriceChangeORM)
                .where(
                    ProductPriceChangeORM.tenant_id == tenant_id,
                    ProductPriceChangeORM.product_id == product_id,
                )
                .order_by(ProductPriceChangeORM.changed_at.asc())
            )
            rows = (await session.execute(stmt)).scalars().all()
            return [
                PriceChange(
                    changed_at=r.changed_at.isoformat(),
                    old_price_amount=r.old_price_amount,
                    new_price_amount=r.new_price_amount,
                )
                for r in rows
            ]


class SqlAlchemyPricingReadModel(PricingReadModel):
    """Precio actual + fecha del último cambio (o creación) por producto activo.
    Tenant-scoped (RLS + filtro); solo lectura."""

    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def base_rows(
        self, tenant_id: str
    ) -> tuple[str, list[ProductPricingBase]]:
        async with self._session_factory() as session:
            currency = await _tenant_currency(session, tenant_id)
            last_changed = (
                select(
                    ProductPriceChangeORM.product_id.label("product_id"),
                    func.max(ProductPriceChangeORM.changed_at).label("last_changed"),
                )
                .where(ProductPriceChangeORM.tenant_id == tenant_id)
                .group_by(ProductPriceChangeORM.product_id)
                .subquery()
            )
            stmt = (
                select(
                    ProductORM.id,
                    ProductORM.name,
                    ProductORM.price_amount,
                    ProductORM.created_at,
                    last_changed.c.last_changed,
                )
                .outerjoin(last_changed, last_changed.c.product_id == ProductORM.id)
                .where(ProductORM.tenant_id == tenant_id, ProductORM.active.is_(True))
                .order_by(ProductORM.name)
            )
            rows = (await session.execute(stmt)).all()
        base = [
            ProductPricingBase(
                product_id=r.id,
                product_name=r.name,
                current_price_amount=r.price_amount,
                last_change_at=r.last_changed or r.created_at,
            )
            for r in rows
        ]
        return currency, base


class SqlAlchemyRotationReadModel(RotationReadModel):
    """Rotación por día de semana (Lun–Dom) desde sale_facts: unidades, ventas y
    el producto más vendido de cada día. Tenant-scoped; solo lectura."""

    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def rotation(
        self,
        tenant_id: str,
        *,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> ProductRotation:
        # Postgres EXTRACT(DOW): 0 = Domingo .. 6 = Sábado.
        dow = func.extract("dow", SaleFactORM.occurred_at)
        async with self._session_factory() as session:
            currency = await _tenant_currency(session, tenant_id)
            stmt = (
                select(
                    dow.label("dow"),
                    SaleFactORM.product_name,
                    func.sum(SaleFactORM.quantity).label("units"),
                    func.sum(SaleFactORM.line_amount).label("sales"),
                )
                .where(SaleFactORM.tenant_id == tenant_id)
                .group_by(dow, SaleFactORM.product_name)
            )
            if since is not None:
                stmt = stmt.where(SaleFactORM.occurred_at >= since)
            if until is not None:
                stmt = stmt.where(SaleFactORM.occurred_at <= until)
            rows = (await session.execute(stmt)).all()

        # Fold a 7 días arrancando en Lunes (0). Trackea top producto por unidades.
        units = [0] * 7
        sales = [0] * 7
        top_name: list[str | None] = [None] * 7
        top_units = [0] * 7
        for r in rows:
            idx = (int(r.dow) + 6) % 7  # Domingo(0)->6, Lunes(1)->0, ...
            u = int(r.units or 0)
            units[idx] += u
            sales[idx] += int(r.sales or 0)
            if u > top_units[idx]:
                top_units[idx] = u
                top_name[idx] = r.product_name
        return ProductRotation(
            currency=currency,
            rows=[
                WeekdayRotationRow(
                    weekday=i,
                    units=units[i],
                    sales_amount=sales[i],
                    top_product_name=top_name[i],
                )
                for i in range(7)
            ],
        )
