"""Resolves a per-tenant TaxJar reporter from the tenant's own credential.

Reporting/AutoFile files under the taxpayer's account, so this is strictly
per-tenant: no shared platform token ever reports a tenant's sales. Returns
``None`` when the tenant hasn't connected TaxJar — the drain then marks those
rows failed (visible, retryable) instead of filing under the wrong account."""

from __future__ import annotations

from app.domain.shared.ports import TokenCipher
from app.domain.tax.credentials_repository import TaxJarCredentialRepository
from app.domain.tax.ports import TaxReporter, TaxReporterResolver
from app.infrastructure.tax.taxjar_reporter import TaxJarReporter


class DbTaxJarReporterResolver(TaxReporterResolver):
    def __init__(
        self, credentials: TaxJarCredentialRepository, cipher: TokenCipher
    ) -> None:
        self._credentials = credentials
        self._cipher = cipher

    async def reporter_for(self, tenant_id: str) -> TaxReporter | None:
        credential = await self._credentials.get_by_tenant(tenant_id)
        if credential is None:
            return None
        token = self._cipher.decrypt(credential.api_token)
        return TaxJarReporter(token, sandbox=credential.sandbox)
