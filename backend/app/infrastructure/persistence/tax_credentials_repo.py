from __future__ import annotations

from sqlalchemy import delete, select

from app.domain.invoice.credentials import TaxCredential
from app.domain.invoice.credentials_repository import TaxCredentialRepository
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.mappers import tax_credential_to_domain, tax_credential_to_orm
from app.infrastructure.persistence.models import TaxCredentialORM


class SqlAlchemyTaxCredentialRepository(TaxCredentialRepository):
    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def get_by_tenant(self, tenant_id: str) -> TaxCredential | None:
        async with self._session_factory() as session:
            row = (
                await session.execute(
                    select(TaxCredentialORM).where(TaxCredentialORM.tenant_id == tenant_id)
                )
            ).scalar_one_or_none()
            return tax_credential_to_domain(row) if row is not None else None

    async def upsert(self, credential: TaxCredential) -> None:
        async with self._session_factory() as session:
            await session.merge(tax_credential_to_orm(credential))

    async def delete(self, tenant_id: str) -> None:
        async with self._session_factory() as session:
            await session.execute(
                delete(TaxCredentialORM).where(TaxCredentialORM.tenant_id == tenant_id)
            )
