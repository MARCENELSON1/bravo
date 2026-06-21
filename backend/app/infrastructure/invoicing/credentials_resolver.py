from __future__ import annotations

from app.domain.invoice.credentials_repository import TaxCredentialRepository
from app.domain.invoice.exceptions import TaxGatewayNotConnected
from app.domain.invoice.ports import ResolvedTaxCredentials, TaxCredentialsResolver
from app.domain.shared.ports import TokenCipher


class DbTaxCredentialsResolver(TaxCredentialsResolver):
    """Returns the tenant's AFIP credentials with cert/key **decrypted** (only in
    memory). Raises ``TaxGatewayNotConnected`` if the tenant has not connected."""

    def __init__(self, credentials: TaxCredentialRepository, cipher: TokenCipher) -> None:
        self._credentials = credentials
        self._cipher = cipher

    async def for_tenant(self, tenant_id: str) -> ResolvedTaxCredentials:
        credential = await self._credentials.get_by_tenant(tenant_id)
        if credential is None:
            raise TaxGatewayNotConnected()
        return ResolvedTaxCredentials(
            cuit=credential.cuit,
            certificate=self._cipher.decrypt(credential.certificate),
            private_key=self._cipher.decrypt(credential.private_key),
            point_of_sale=credential.point_of_sale,
            fiscal_condition=credential.fiscal_condition,
            live_mode=credential.live_mode,
        )
