"""Connect a tenant's own TaxJar account (its API token). The token is encrypted
before persisting — same pattern as AFIP credentials / MercadoPago OAuth.

Reporting/AutoFile files under the taxpayer's account, so each tenant connects
their own; there is no shared platform account for reporting."""

from __future__ import annotations

from uuid import uuid4

from app.domain.identity.ports import TenantContext
from app.domain.shared.ports import TokenCipher
from app.domain.tax.credentials import TaxJarCredential
from app.domain.tax.credentials_repository import TaxJarCredentialRepository


class ConnectTaxJar:
    def __init__(
        self,
        credentials: TaxJarCredentialRepository,
        cipher: TokenCipher,
        tenant_context: TenantContext,
    ) -> None:
        self._credentials = credentials
        self._cipher = cipher
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str, api_token: str, sandbox: bool = True) -> None:
        self._tenant_context.set(tenant_id)
        existing = await self._credentials.get_by_tenant(tenant_id)
        credential = TaxJarCredential(
            id=existing.id if existing is not None else str(uuid4()),
            tenant_id=tenant_id,
            api_token=self._cipher.encrypt(api_token),
            sandbox=sandbox,
        )
        await self._credentials.upsert(credential)


class GetTaxJarConnection:
    def __init__(
        self, credentials: TaxJarCredentialRepository, tenant_context: TenantContext
    ) -> None:
        self._credentials = credentials
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str) -> TaxJarCredential | None:
        self._tenant_context.set(tenant_id)
        return await self._credentials.get_by_tenant(tenant_id)


class DisconnectTaxJar:
    def __init__(
        self, credentials: TaxJarCredentialRepository, tenant_context: TenantContext
    ) -> None:
        self._credentials = credentials
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str) -> None:
        self._tenant_context.set(tenant_id)
        await self._credentials.delete(tenant_id)
