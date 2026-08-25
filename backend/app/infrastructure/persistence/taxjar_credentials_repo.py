from __future__ import annotations

from sqlalchemy import delete, select

from app.domain.tax.credentials import TaxJarCredential
from app.domain.tax.credentials_repository import TaxJarCredentialRepository
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.mappers import (
    taxjar_credential_to_domain,
    taxjar_credential_to_orm,
)
from app.infrastructure.persistence.models import TaxJarCredentialORM


class SqlAlchemyTaxJarCredentialRepository(TaxJarCredentialRepository):
    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def get_by_tenant(self, tenant_id: str) -> TaxJarCredential | None:
        async with self._session_factory() as session:
            row = (
                await session.execute(
                    select(TaxJarCredentialORM).where(
                        TaxJarCredentialORM.tenant_id == tenant_id
                    )
                )
            ).scalar_one_or_none()
            return taxjar_credential_to_domain(row) if row is not None else None

    async def upsert(self, credential: TaxJarCredential) -> None:
        async with self._session_factory() as session:
            await session.merge(taxjar_credential_to_orm(credential))

    async def delete(self, tenant_id: str) -> None:
        async with self._session_factory() as session:
            await session.execute(
                delete(TaxJarCredentialORM).where(
                    TaxJarCredentialORM.tenant_id == tenant_id
                )
            )
