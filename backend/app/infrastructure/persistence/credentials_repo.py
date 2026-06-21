from __future__ import annotations

from sqlalchemy import delete, select

from app.domain.payment.credentials import PaymentCredential
from app.domain.payment.credentials_repository import PaymentCredentialRepository
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.mappers import (
    payment_credential_to_domain,
    payment_credential_to_orm,
)
from app.infrastructure.persistence.models import PaymentCredentialORM


class SqlAlchemyPaymentCredentialRepository(PaymentCredentialRepository):
    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def get_by_tenant(self, tenant_id: str, provider: str) -> PaymentCredential | None:
        async with self._session_factory() as session:
            stmt = select(PaymentCredentialORM).where(
                PaymentCredentialORM.tenant_id == tenant_id,
                PaymentCredentialORM.provider == provider,
            )
            row = (await session.execute(stmt)).scalar_one_or_none()
            return payment_credential_to_domain(row) if row is not None else None

    async def get_by_account_id(self, external_account_id: str) -> PaymentCredential | None:
        # Cross-tenant lookup for the webhook (no tenant context yet). Runs under
        # an RLS-exempt session — see the webhook wiring in the OAuth tramo.
        async with self._session_factory() as session:
            stmt = select(PaymentCredentialORM).where(
                PaymentCredentialORM.external_account_id == external_account_id
            )
            row = (await session.execute(stmt)).scalar_one_or_none()
            return payment_credential_to_domain(row) if row is not None else None

    async def upsert(self, credential: PaymentCredential) -> None:
        async with self._session_factory() as session:
            await session.merge(payment_credential_to_orm(credential))

    async def delete(self, tenant_id: str, provider: str) -> None:
        async with self._session_factory() as session:
            await session.execute(
                delete(PaymentCredentialORM).where(
                    PaymentCredentialORM.tenant_id == tenant_id,
                    PaymentCredentialORM.provider == provider,
                )
            )
