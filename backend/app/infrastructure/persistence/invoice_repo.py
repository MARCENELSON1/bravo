from __future__ import annotations

from sqlalchemy import select

from app.domain.invoice.entities import Invoice
from app.domain.invoice.repository import InvoiceRepository
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.mappers import invoice_to_domain, invoice_to_orm
from app.infrastructure.persistence.models import InvoiceORM


class SqlAlchemyInvoiceRepository(InvoiceRepository):
    """Every query is scoped by ``tenant_id`` (defence in depth on top of RLS)."""

    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def get_by_id(self, tenant_id: str, invoice_id: str) -> Invoice | None:
        async with self._session_factory() as session:
            row = (
                await session.execute(
                    select(InvoiceORM).where(
                        InvoiceORM.id == invoice_id, InvoiceORM.tenant_id == tenant_id
                    )
                )
            ).scalar_one_or_none()
            return invoice_to_domain(row) if row is not None else None

    async def get_by_order(self, tenant_id: str, order_id: str) -> Invoice | None:
        async with self._session_factory() as session:
            row = (
                await session.execute(
                    select(InvoiceORM).where(
                        InvoiceORM.order_id == order_id, InvoiceORM.tenant_id == tenant_id
                    )
                )
            ).scalar_one_or_none()
            return invoice_to_domain(row) if row is not None else None

    async def list(self, tenant_id: str) -> list[Invoice]:
        async with self._session_factory() as session:
            rows = (
                await session.execute(
                    select(InvoiceORM)
                    .where(InvoiceORM.tenant_id == tenant_id)
                    .order_by(InvoiceORM.created_at.desc())
                )
            ).scalars().all()
            return [invoice_to_domain(row) for row in rows]

    async def add(self, invoice: Invoice) -> None:
        async with self._session_factory() as session:
            session.add(invoice_to_orm(invoice))

    async def save(self, invoice: Invoice) -> None:
        async with self._session_factory() as session:
            await session.merge(invoice_to_orm(invoice))
