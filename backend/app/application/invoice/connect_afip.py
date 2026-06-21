"""Connect a tenant's AFIP account (its CUIT + certificate). Cert and key are
encrypted before persisting (same pattern as MercadoPago OAuth, Fase 3.5)."""

from __future__ import annotations

from uuid import uuid4

from app.domain.identity.ports import TenantContext
from app.domain.invoice.credentials import TaxCredential
from app.domain.invoice.credentials_repository import TaxCredentialRepository
from app.domain.invoice.value_objects import FiscalCondition
from app.domain.shared.ports import TokenCipher


class ConnectAfip:
    def __init__(
        self,
        credentials: TaxCredentialRepository,
        cipher: TokenCipher,
        tenant_context: TenantContext,
    ) -> None:
        self._credentials = credentials
        self._cipher = cipher
        self._tenant_context = tenant_context

    async def execute(
        self,
        *,
        tenant_id: str,
        cuit: str,
        certificate: str,
        private_key: str,
        point_of_sale: int,
        fiscal_condition: str,
    ) -> None:
        self._tenant_context.set(tenant_id)
        existing = await self._credentials.get_by_tenant(tenant_id)
        credential = TaxCredential(
            id=existing.id if existing is not None else str(uuid4()),
            tenant_id=tenant_id,
            cuit=cuit,
            certificate=self._cipher.encrypt(certificate),
            private_key=self._cipher.encrypt(private_key),
            point_of_sale=point_of_sale,
            fiscal_condition=FiscalCondition(fiscal_condition),
            live_mode=False,
        )
        await self._credentials.upsert(credential)


class GetAfipConnection:
    def __init__(
        self, credentials: TaxCredentialRepository, tenant_context: TenantContext
    ) -> None:
        self._credentials = credentials
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str) -> TaxCredential | None:
        self._tenant_context.set(tenant_id)
        return await self._credentials.get_by_tenant(tenant_id)


class DisconnectAfip:
    def __init__(
        self, credentials: TaxCredentialRepository, tenant_context: TenantContext
    ) -> None:
        self._credentials = credentials
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str) -> None:
        self._tenant_context.set(tenant_id)
        await self._credentials.delete(tenant_id)
