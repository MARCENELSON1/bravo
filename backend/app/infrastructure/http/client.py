"""Shared outbound HTTP connection pool.

Every outbound adapter used to build a brand new ``httpx.AsyncClient`` per call,
paying a full TCP + TLS handshake each time — including on the charge path.

What is worth sharing is the *transport*: that is what owns the connection pool
and the TLS sessions. The clients themselves stay per-adapter, so each keeps its
own ``base_url`` and its own credentials. That distinction matters: MercadoPago
authenticates with a **per-tenant** token, and a client shared across tenants
would risk carrying one tenant's Authorization header into another's request.
Sharing only the pool makes that class of bug impossible by construction.
"""

from __future__ import annotations

import httpx

# Connections idle longer than this are dropped; keeps the pool from holding
# sockets that an upstream proxy has already closed.
_KEEPALIVE_EXPIRY_S = 30.0


class _SharedTransport(httpx.AsyncBaseTransport):
    """Hands requests to a transport it does not own.

    ``AsyncClient.aclose()`` closes its transport, and adapters use their client
    as a context manager — so handing them the pooled transport directly would
    tear the pool down after the first call. This wrapper swallows that close;
    the real one happens once, at shutdown, via :meth:`HttpClientProvider.aclose`.
    """

    def __init__(self, inner: httpx.AsyncBaseTransport) -> None:
        self._inner = inner

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        return await self._inner.handle_async_request(request)

    async def aclose(self) -> None:  # noqa: D102 - intentionally a no-op
        return None


class HttpClientProvider:
    """Owns the process-wide outbound connection pool.

    Adapters ask for a transport and build their own client around it, keeping
    their base URL and credentials to themselves. Tests keep injecting their own
    ``httpx.MockTransport``, which simply bypasses this provider.
    """

    def __init__(
        self,
        *,
        timeout_s: float = 10.0,
        max_connections: int = 100,
        max_keepalive_connections: int = 20,
    ) -> None:
        self._timeout = httpx.Timeout(timeout_s)
        self._limits = httpx.Limits(
            max_connections=max_connections,
            max_keepalive_connections=max_keepalive_connections,
            keepalive_expiry=_KEEPALIVE_EXPIRY_S,
        )
        self._transport: httpx.AsyncHTTPTransport | None = None

    @property
    def timeout(self) -> httpx.Timeout:
        return self._timeout

    def transport(self) -> httpx.AsyncBaseTransport:
        """A pooled transport safe to hand to a short-lived client."""
        if self._transport is None:
            self._transport = httpx.AsyncHTTPTransport(limits=self._limits)
        return _SharedTransport(self._transport)

    async def aclose(self) -> None:
        """Release the pool. Called once, from the application lifespan."""
        if self._transport is not None:
            await self._transport.aclose()
            self._transport = None
