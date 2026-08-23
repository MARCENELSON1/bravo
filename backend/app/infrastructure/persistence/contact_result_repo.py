from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select

from app.application.contact.use_cases import ContactResult, ContactResultReadModel
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.models import (
    ContactLogORM,
    OrderORM,
    SaleFactORM,
    TenantORM,
)


class SqlAlchemyContactResultReadModel(ContactResultReadModel):
    """El loop de resultado: de los clientes contactados desde ``since``, cuántos
    tuvieron una venta atribuida DESPUÉS de su primer contacto, y cuánto gastaron.
    Tenant-scoped; read-only."""

    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def result(self, tenant_id: str, *, since: datetime) -> ContactResult:
        async with self._session_factory() as db:
            currency = (
                await db.execute(
                    select(TenantORM.currency).where(TenantORM.id == tenant_id)
                )
            ).scalar_one_or_none() or "ARS"

            # Primer contacto por cliente en la ventana.
            first_contact = dict(
                (
                    await db.execute(
                        select(
                            ContactLogORM.customer_id,
                            func.min(ContactLogORM.contacted_at),
                        )
                        .where(
                            ContactLogORM.tenant_id == tenant_id,
                            ContactLogORM.contacted_at >= since,
                        )
                        .group_by(ContactLogORM.customer_id)
                    )
                ).all()
            )
            if not first_contact:
                return ContactResult(
                    currency=currency, contacted=0, returned=0, revenue=0
                )

            # Ventas atribuidas de esos clientes (se filtran por fecha en Python,
            # porque el umbral es distinto por cliente).
            sales = (
                await db.execute(
                    select(
                        OrderORM.customer_id,
                        SaleFactORM.occurred_at,
                        SaleFactORM.line_amount,
                    )
                    .select_from(SaleFactORM)
                    .join(OrderORM, OrderORM.id == SaleFactORM.order_id)
                    .where(
                        SaleFactORM.tenant_id == tenant_id,
                        OrderORM.customer_id.in_(list(first_contact.keys())),
                    )
                )
            ).all()

        returned: set[str] = set()
        revenue = 0
        for customer_id, occurred_at, line_amount in sales:
            if occurred_at > first_contact[customer_id]:
                returned.add(customer_id)
                revenue += int(line_amount)

        return ContactResult(
            currency=currency,
            contacted=len(first_contact),
            returned=len(returned),
            revenue=revenue,
        )
