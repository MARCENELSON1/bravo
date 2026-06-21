from __future__ import annotations

from sqlalchemy import select

from app.domain.payment.entities import Payment
from app.domain.payment.repository import PaymentRepository
from app.domain.payment.value_objects import PaymentDirection
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.mappers import payment_to_domain, payment_to_orm
from app.infrastructure.persistence.models import PaymentORM


class SqlAlchemyPaymentRepository(PaymentRepository):
    """Every query is scoped by ``tenant_id`` (defence in depth on top of RLS)."""

    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def get_by_id(self, tenant_id: str, payment_id: str) -> Payment | None:
        async with self._session_factory() as session:
            stmt = select(PaymentORM).where(
                PaymentORM.id == payment_id, PaymentORM.tenant_id == tenant_id
            )
            row = (await session.execute(stmt)).scalar_one_or_none()
            return payment_to_domain(row) if row is not None else None

    async def get_by_external_ref(self, tenant_id: str, external_ref: str) -> Payment | None:
        async with self._session_factory() as session:
            stmt = select(PaymentORM).where(
                PaymentORM.external_ref == external_ref, PaymentORM.tenant_id == tenant_id
            )
            row = (await session.execute(stmt)).scalar_one_or_none()
            return payment_to_domain(row) if row is not None else None

    async def list_by_order(self, tenant_id: str, order_id: str) -> list[Payment]:
        async with self._session_factory() as session:
            stmt = (
                select(PaymentORM)
                .where(PaymentORM.tenant_id == tenant_id, PaymentORM.order_id == order_id)
                .order_by(PaymentORM.created_at)
            )
            rows = (await session.execute(stmt)).scalars().all()
            return [payment_to_domain(row) for row in rows]

    async def list_expenses(self, tenant_id: str) -> list[Payment]:
        async with self._session_factory() as session:
            stmt = (
                select(PaymentORM)
                .where(
                    PaymentORM.tenant_id == tenant_id,
                    PaymentORM.direction == PaymentDirection.OUTFLOW.value,
                )
                .order_by(PaymentORM.created_at.desc())
            )
            rows = (await session.execute(stmt)).scalars().all()
            return [payment_to_domain(row) for row in rows]

    async def add(self, payment: Payment) -> None:
        async with self._session_factory() as session:
            session.add(payment_to_orm(payment))

    async def save(self, payment: Payment) -> None:
        async with self._session_factory() as session:
            await session.merge(payment_to_orm(payment))
