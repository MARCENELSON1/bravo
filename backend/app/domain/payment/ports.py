from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.domain.payment.entities import Payment
from app.domain.payment.value_objects import PaymentStatus


class PaymentGateway(ABC):
    """Port to initiate/confirm a charge.

    The MVP uses ``ManualPaymentGateway`` (the money already moved outside the
    system → confirms immediately). MercadoPago / QR / Payway adapters slot in
    behind this same port and may return PENDING until a webhook confirms.
    """

    @abstractmethod
    async def charge(self, *, payment: Payment) -> Payment: ...


@dataclass(frozen=True)
class GatewayChargeStatus:
    """Normalised view of a charge as reported by the gateway (via webhook
    polling). ``external_reference`` is the value we sent when creating the
    charge (``"<tenant_id>:<payment_id>"``) so the notification can be routed
    back to the right tenant and payment without a user token."""

    gateway_payment_id: str
    external_reference: str | None
    status: PaymentStatus


class PaymentNotificationGateway(ABC):
    """Port for inbound gateway notifications (webhooks).

    Implemented only by online gateways (MercadoPago). ``verify_signature``
    authenticates the request (the endpoint is public); ``fetch_status`` asks
    the gateway for the authoritative status — notifications are not trusted at
    face value."""

    @abstractmethod
    def verify_signature(
        self,
        *,
        data_id: str | None,
        request_id: str | None,
        ts: str | None,
        received_hmac: str,
    ) -> bool: ...

    @abstractmethod
    async def fetch_status(
        self, *, gateway_payment_id: str, access_token: str | None = None
    ) -> GatewayChargeStatus: ...


@dataclass(frozen=True)
class OAuthTokens:
    """Result of an OAuth code exchange / refresh with a payment provider."""

    access_token: str
    refresh_token: str | None
    public_key: str | None
    external_account_id: str  # the seller's provider user_id
    live_mode: bool
    expires_in: int | None  # seconds until the access token expires


class OAuthPaymentProvider(ABC):
    """Port for the OAuth 'connect your account' flow (Fase 3.5). Each tenant
    authorises NÚCLEO to charge on behalf of its own provider account."""

    @abstractmethod
    def authorization_url(self, *, state: str, redirect_uri: str) -> str: ...

    @abstractmethod
    async def exchange_code(self, *, code: str, redirect_uri: str) -> OAuthTokens: ...

    @abstractmethod
    async def refresh(self, *, refresh_token: str) -> OAuthTokens: ...

    @abstractmethod
    async def fetch_nickname(self, *, access_token: str) -> str | None: ...


@dataclass(frozen=True)
class ResolvedCredentials:
    access_token: str
    live_mode: bool


class PaymentCredentialsResolver(ABC):
    """Resolves the VIGENTE access token for a tenant (refreshing + persisting if
    expired). ``tenant_for_account`` maps a provider seller id back to a tenant
    (used by the webhook, which has no tenant context)."""

    @abstractmethod
    async def for_tenant(self, tenant_id: str) -> ResolvedCredentials: ...

    @abstractmethod
    async def tenant_for_account(self, external_account_id: str) -> str | None: ...
