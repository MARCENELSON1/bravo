from __future__ import annotations

from sqlalchemy import delete, or_, select

from app.domain.customer.entities import Customer
from app.domain.customer.repository import CustomerRepository
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.mappers import (
    customer_to_domain,
    customer_to_orm,
)
from app.infrastructure.persistence.models import CustomerORM


class SqlAlchemyCustomerRepository(CustomerRepository):
    """Every query is scoped by ``tenant_id`` (defence in depth on top of RLS)."""

    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def get_by_id(self, tenant_id: str, customer_id: str) -> Customer | None:
        async with self._session_factory() as db:
            stmt = select(CustomerORM).where(
                CustomerORM.id == customer_id, CustomerORM.tenant_id == tenant_id
            )
            row = (await db.execute(stmt)).scalar_one_or_none()
            return customer_to_domain(row) if row is not None else None

    async def list(self, tenant_id: str, *, search: str | None = None) -> list[Customer]:
        async with self._session_factory() as db:
            stmt = select(CustomerORM).where(CustomerORM.tenant_id == tenant_id)
            if search:
                like = f"%{search.strip()}%"
                stmt = stmt.where(
                    or_(CustomerORM.name.ilike(like), CustomerORM.phone.ilike(like))
                )
            stmt = stmt.order_by(CustomerORM.name)
            rows = (await db.execute(stmt)).scalars().all()
            return [customer_to_domain(row) for row in rows]

    async def add(self, customer: Customer) -> None:
        async with self._session_factory() as db:
            db.add(customer_to_orm(customer))

    async def save(self, customer: Customer) -> None:
        async with self._session_factory() as db:
            await db.merge(customer_to_orm(customer))

    async def delete(self, tenant_id: str, customer_id: str) -> None:
        async with self._session_factory() as db:
            await db.execute(
                delete(CustomerORM).where(
                    CustomerORM.id == customer_id, CustomerORM.tenant_id == tenant_id
                )
            )
