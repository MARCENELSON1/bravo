"""OAuth 'connect MercadoPago' use cases (Fase 3.5).

The ``state`` is an HMAC-signed, time-bounded token carrying the tenant id, so
the public callback can be trusted (anti-CSRF) and routed to the right tenant.
Tokens are encrypted before they are persisted.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.domain.identity.ports import TenantContext
from app.domain.payment.credentials import (
    ConnectionStatus,
    PaymentCredential,
    PaymentProvider,
)
from app.domain.payment.credentials_repository import PaymentCredentialRepository
from app.domain.payment.exceptions import InvalidOAuthState
from app.domain.payment.ports import OAuthPaymentProvider
from app.domain.shared.ports import TokenCipher

_PROVIDER = PaymentProvider.MERCADOPAGO.value


def sign_oauth_state(secret: str, tenant_id: str, issued_at: int) -> str:
    payload = base64.urlsafe_b64encode(
        json.dumps({"t": tenant_id, "iat": issued_at}).encode()
    ).decode()
    sig = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{sig}"


def verify_oauth_state(secret: str, state: str, now: int, max_age_s: int) -> str | None:
    payload, _, sig = state.partition(".")
    if not payload or not sig:
        return None
    expected = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, sig):
        return None
    try:
        data = json.loads(base64.urlsafe_b64decode(payload.encode()))
    except (ValueError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict) or "t" not in data or "iat" not in data:
        return None
    if now - int(data["iat"]) > max_age_s:
        return None
    return str(data["t"])


def _expiry(expires_in: int | None) -> datetime | None:
    if not expires_in:
        return None
    return datetime.now(UTC) + timedelta(seconds=expires_in)


class StartMercadoPagoConnection:
    def __init__(
        self,
        oauth: OAuthPaymentProvider,
        tenant_context: TenantContext,
        state_secret: str,
        redirect_uri: str,
    ) -> None:
        self._oauth = oauth
        self._tenant_context = tenant_context
        self._state_secret = state_secret
        self._redirect_uri = redirect_uri

    async def execute(self, *, tenant_id: str) -> str:
        self._tenant_context.set(tenant_id)
        state = sign_oauth_state(self._state_secret, tenant_id, int(time.time()))
        return self._oauth.authorization_url(state=state, redirect_uri=self._redirect_uri)


class CompleteMercadoPagoConnection:
    def __init__(
        self,
        oauth: OAuthPaymentProvider,
        credentials: PaymentCredentialRepository,
        cipher: TokenCipher,
        tenant_context: TenantContext,
        state_secret: str,
        redirect_uri: str,
        state_ttl_min: int,
    ) -> None:
        self._oauth = oauth
        self._credentials = credentials
        self._cipher = cipher
        self._tenant_context = tenant_context
        self._state_secret = state_secret
        self._redirect_uri = redirect_uri
        self._state_ttl_s = state_ttl_min * 60

    async def execute(self, *, code: str, state: str) -> None:
        tenant_id = verify_oauth_state(
            self._state_secret, state, int(time.time()), self._state_ttl_s
        )
        if tenant_id is None:
            raise InvalidOAuthState()
        self._tenant_context.set(tenant_id)
        tokens = await self._oauth.exchange_code(code=code, redirect_uri=self._redirect_uri)
        nickname = await self._oauth.fetch_nickname(access_token=tokens.access_token)
        existing = await self._credentials.get_by_tenant(tenant_id, _PROVIDER)
        credential = PaymentCredential(
            id=existing.id if existing is not None else str(uuid4()),
            tenant_id=tenant_id,
            provider=PaymentProvider.MERCADOPAGO,
            external_account_id=tokens.external_account_id,
            access_token=self._cipher.encrypt(tokens.access_token),
            refresh_token=(
                self._cipher.encrypt(tokens.refresh_token) if tokens.refresh_token else None
            ),
            public_key=tokens.public_key,
            nickname=nickname,
            expires_at=_expiry(tokens.expires_in),
            live_mode=tokens.live_mode,
            status=ConnectionStatus.CONNECTED,
        )
        await self._credentials.upsert(credential)


class DisconnectMercadoPago:
    def __init__(
        self, credentials: PaymentCredentialRepository, tenant_context: TenantContext
    ) -> None:
        self._credentials = credentials
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str) -> None:
        self._tenant_context.set(tenant_id)
        await self._credentials.delete(tenant_id, _PROVIDER)


class GetMercadoPagoConnection:
    def __init__(
        self, credentials: PaymentCredentialRepository, tenant_context: TenantContext
    ) -> None:
        self._credentials = credentials
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str) -> PaymentCredential | None:
        self._tenant_context.set(tenant_id)
        return await self._credentials.get_by_tenant(tenant_id, _PROVIDER)
