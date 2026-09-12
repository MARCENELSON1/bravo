"""The outbound connection pool is shared; credentials are not.

Adapters used to build a fresh ``httpx.AsyncClient`` per call, paying a TCP+TLS
handshake every time. They now share one pooled *transport* while keeping their
own client — which is what keeps MercadoPago's per-tenant token from ever
leaking into another tenant's request.
"""

from __future__ import annotations

import httpx
import pytest

from app.domain.payment.entities import Payment
from app.domain.payment.ports import PaymentCredentialsResolver, ResolvedCredentials
from app.domain.payment.value_objects import PaymentDirection, PaymentMethod, PaymentStatus
from app.domain.shared.money import Money
from app.infrastructure.http.client import HttpClientProvider
from app.infrastructure.payments.mercadopago_gateway import MercadoPagoGateway


async def test_transport_is_pooled_across_clients():
    provider = HttpClientProvider()
    first, second = provider.transport(), provider.transport()

    # Different handles, one underlying pool.
    assert first is not second
    assert first._inner is second._inner


async def test_client_close_does_not_tear_down_the_shared_pool():
    """Adapters use their client as a context manager.

    ``AsyncClient.aclose()`` closes its transport, so without the guard the
    first adapter to finish would destroy the pool for everyone else.
    """
    provider = HttpClientProvider()
    pool = provider.transport()._inner

    async with httpx.AsyncClient(transport=provider.transport()):
        pass

    assert provider.transport()._inner is pool


async def test_provider_close_releases_the_pool():
    provider = HttpClientProvider()
    pool = provider.transport()._inner

    await provider.aclose()

    assert provider.transport()._inner is not pool


async def test_every_call_goes_through_the_one_pooled_transport():
    """Three calls from three short-lived clients hit a single transport.

    That is what makes connection reuse possible: the pool lives in the
    transport, so it outlives the clients that borrow it.
    """

    class _CountingTransport(httpx.AsyncBaseTransport):
        def __init__(self) -> None:
            self.handled = 0

        async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
            self.handled += 1
            return httpx.Response(200, text="ok")

    provider = HttpClientProvider()
    counting = _CountingTransport()
    provider._transport = counting  # type: ignore[assignment]

    for _ in range(3):
        async with httpx.AsyncClient(transport=provider.transport()) as client:
            await client.get("https://example.test/ping")

    assert counting.handled == 3
    assert provider.transport()._inner is counting


class _TenantResolver(PaymentCredentialsResolver):
    """Hands each tenant its own MercadoPago token, as the real one does."""

    def __init__(self, tokens: dict[str, str]) -> None:
        self._tokens = tokens

    async def for_tenant(self, tenant_id: str) -> ResolvedCredentials:
        return ResolvedCredentials(access_token=self._tokens[tenant_id], live_mode=False)

    async def tenant_for_account(self, external_account_id: str) -> str | None:
        return None


def _payment(tenant_id: str) -> Payment:
    return Payment(
        id=f"pay-{tenant_id}",
        tenant_id=tenant_id,
        direction=PaymentDirection.INFLOW,
        amount=Money(300000, "ARS"),
        method=PaymentMethod.MERCADOPAGO,
        status=PaymentStatus.PENDING,
    )


@pytest.mark.parametrize("order", [("t1", "t2"), ("t2", "t1")])
async def test_shared_pool_never_mixes_tenant_credentials(order):
    """Two tenants charging over the same pool must not see each other's token."""
    seen: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.url.path, request.headers.get("Authorization", "")))
        return httpx.Response(
            201,
            json={
                "id": "pref-1",
                "init_point": "https://mp/checkout/prod",
                "sandbox_init_point": "https://mp/checkout/sandbox",
            },
        )

    provider = HttpClientProvider()
    provider._transport = httpx.MockTransport(handler)  # type: ignore[assignment]

    gateway = MercadoPagoGateway(
        credentials_resolver=_TenantResolver({"t1": "TOKEN-t1", "t2": "TOKEN-t2"}),
        webhook_secret="s3cret",
        notification_url="https://hook.example/api/v1/webhooks/mercadopago",
        access_token="TEST-app-fetch",
        transport=provider.transport(),
    )

    for tenant_id in order:
        await gateway.charge(payment=_payment(tenant_id))

    assert [auth for _, auth in seen] == [f"Bearer TOKEN-{t}" for t in order]
