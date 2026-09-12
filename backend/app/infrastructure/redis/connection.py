"""Process-wide Redis connectivity, shared by the cache, the bus and the limiter.

Three adapters need Redis and each used to be free to build its own client; that
would mean three connection pools per process for one server. This provider owns
them instead, the same way :class:`HttpClientProvider` owns the outbound HTTP
pool, and the application lifespan closes it once.

Two clients, on purpose. Commands (``GET``/``SET``/``EVAL``) run against a
short-timeout client: a cache read must never outlast the query it replaces, and
a rate-limit check must never hold a request. Pub/Sub cannot live under that
budget — listening is a long blocking read, so a 200 ms socket timeout would
tear the subscription down between events. It gets its own client with no read
timeout.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Same budget the cache adapter used before this provider existed.
_COMMAND_TIMEOUT_S = 0.2
# Connecting is allowed to take longer than a command: a cold TCP + auth
# handshake against a managed Redis routinely exceeds 200 ms, and failing it
# would leave the adapter permanently degraded on the first call after a deploy.
_CONNECT_TIMEOUT_S = 2.0


class RedisProvider:
    """Owns the Redis clients for this process.

    Every accessor is **fail-soft**: if the driver is missing or the URL is
    unusable it returns ``None`` and logs, so callers degrade (cache miss, event
    dropped, rate limit allowed) instead of raising. Clients are built lazily, so
    importing this module never needs a reachable Redis — which keeps the default
    ``memory`` backends free of any Redis dependency at import time.
    """

    def __init__(
        self,
        url: str,
        *,
        command_timeout_s: float = _COMMAND_TIMEOUT_S,
        connect_timeout_s: float = _CONNECT_TIMEOUT_S,
    ) -> None:
        self._url = url
        self._command_timeout = command_timeout_s
        self._connect_timeout = connect_timeout_s
        self._client: Any | None = None
        self._pubsub_client: Any | None = None

    def client(self) -> Any | None:
        """Client for regular commands (short read timeout)."""
        if self._client is None:
            self._client = self._build(socket_timeout=self._command_timeout)
        return self._client

    def pubsub_client(self) -> Any | None:
        """Client for Pub/Sub: no read timeout, since listening blocks.

        ``Redis.pubsub()`` checks out its own connection from this client's pool,
        so a subscriber never competes with a command for the same socket.
        """
        if self._pubsub_client is None:
            self._pubsub_client = self._build(socket_timeout=None)
        return self._pubsub_client

    def _build(self, *, socket_timeout: float | None) -> Any | None:
        try:
            from redis.asyncio import Redis

            return Redis.from_url(
                self._url,
                socket_timeout=socket_timeout,
                socket_connect_timeout=self._connect_timeout,
                # Payloads are pickled (cache) or JSON (bus); decoding is the
                # caller's business, so keep raw bytes here.
                decode_responses=False,
            )
        except Exception:  # pragma: no cover - missing driver / malformed URL
            logger.warning("redis unavailable at %s; adapters will degrade", self._url)
            return None

    async def aclose(self) -> None:
        """Release both pools. Called once, from the application lifespan."""
        for client in (self._client, self._pubsub_client):
            if client is None:
                continue
            try:
                await client.aclose()
            except Exception:  # pragma: no cover - best effort on shutdown
                logger.debug("redis close failed", exc_info=True)
        self._client = None
        self._pubsub_client = None
