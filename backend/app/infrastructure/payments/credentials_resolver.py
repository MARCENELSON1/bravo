"""Resolves a tenant's vigente MercadoPago access token (Fase 3.5).

Decrypts the stored token; if expired and a refresh token exists, refreshes it
via OAuth and persists the rotated tokens. Falls back to the app-level
``MP_ACCESS_TOKEN`` (env) only when a tenant has not connected — a transition aid
for dev/single-account; in prod that fallback should be empty so an unconnected
tenant gets ``PaymentGatewayNotConnected`` instead of charging the wrong account.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.domain.payment.credentials import PaymentProvider
from app.domain.payment.credentials_repository import PaymentCredentialRepository
from app.domain.payment.exceptions import PaymentGatewayNotConnected
from app.domain.payment.ports import (
    OAuthPaymentProvider,
    PaymentCredentialsResolver,
    ResolvedCredentials,
)
from app.domain.shared.ports import TokenCipher

_PROVIDER = PaymentProvider.MERCADOPAGO.value


class DbPaymentCredentialsResolver(PaymentCredentialsResolver):
    def __init__(
        self,
        credentials: PaymentCredentialRepository,
        oauth: OAuthPaymentProvider,
        cipher: TokenCipher,
        fallback_token: str = "",
    ) -> None:
        self._credentials = credentials
        self._oauth = oauth
        self._cipher = cipher
        self._fallback_token = fallback_token

    async def for_tenant(self, tenant_id: str) -> ResolvedCredentials:
        credential = await self._credentials.get_by_tenant(tenant_id, _PROVIDER)
        if credential is None:
            if self._fallback_token:
                return ResolvedCredentials(
                    access_token=self._fallback_token,
                    live_mode=not self._fallback_token.startswith("TEST-"),
                )
            raise PaymentGatewayNotConnected()

        access_token = self._cipher.decrypt(credential.access_token)
        expired = (
            credential.expires_at is not None
            and credential.expires_at <= datetime.now(UTC)
        )
        if expired and credential.refresh_token is not None:
            tokens = await self._oauth.refresh(
                refresh_token=self._cipher.decrypt(credential.refresh_token)
            )
            access_token = tokens.access_token
            credential.access_token = self._cipher.encrypt(tokens.access_token)
            if tokens.refresh_token is not None:
                credential.refresh_token = self._cipher.encrypt(tokens.refresh_token)
            if tokens.expires_in:
                credential.expires_at = datetime.now(UTC) + timedelta(
                    seconds=tokens.expires_in
                )
            credential.live_mode = tokens.live_mode
            await self._credentials.upsert(credential)

        return ResolvedCredentials(access_token=access_token, live_mode=credential.live_mode)

    async def tenant_for_account(self, external_account_id: str) -> str | None:
        credential = await self._credentials.get_by_account_id(external_account_id)
        return credential.tenant_id if credential is not None else None
