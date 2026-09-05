from __future__ import annotations

import logging
import pickle
from typing import Any

from app.domain.shared.cache import CachePort

logger = logging.getLogger(__name__)

# A cache read must never be slower than the query it replaces, so the backend
# gets a hard budget: past this, we give up and hit the database instead.
_TIMEOUT_SECONDS = 0.2
# Namespace versions outlive the entries they guard; without this an idle
# tenant's counter would live forever.
_VERSION_TTL_SECONDS = 24 * 60 * 60


class RedisCache(CachePort):
    """Redis-backed cache, shared across replicas.

    Same contract as :class:`InMemoryCache`, but the entries live outside the
    process: an invalidation on one replica is seen by every other one
    immediately, which is what makes horizontal scaling safe for cached catalog
    data. Values are domain entities (not JSON-serializable), so they travel as
    pickle — safe here because the payloads are written and read only by this
    application, never by an untrusted producer.

    **Fail-open by design**: every operation swallows backend errors and
    timeouts, logging at debug level. A Redis outage degrades the system to
    "always miss" (slower, still correct) instead of taking it down.
    """

    def __init__(self, url: str, timeout_seconds: float = _TIMEOUT_SECONDS) -> None:
        self._url = url
        self._timeout = timeout_seconds
        self._client: Any | None = None

    def _get_client(self) -> Any | None:
        """Lazily build the client so importing the module never needs Redis."""
        if self._client is None:
            try:
                from redis.asyncio import Redis

                self._client = Redis.from_url(
                    self._url,
                    socket_timeout=self._timeout,
                    socket_connect_timeout=self._timeout,
                )
            except Exception:  # pragma: no cover - misconfigured URL / missing dep
                logger.warning("redis cache unavailable, falling back to no cache")
                return None
        return self._client

    async def get(self, key: str) -> Any | None:
        client = self._get_client()
        if client is None:
            return None
        try:
            raw = await client.get(key)
        except Exception:
            logger.debug("cache get failed for %s", key, exc_info=True)
            return None
        if raw is None:
            return None
        try:
            return pickle.loads(raw)
        except Exception:
            # A stale payload from an older deploy: treat as a miss and move on.
            logger.debug("cache decode failed for %s", key, exc_info=True)
            return None

    async def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        client = self._get_client()
        if client is None:
            return
        try:
            await client.set(key, pickle.dumps(value), ex=ttl_seconds)
        except Exception:
            logger.debug("cache set failed for %s", key, exc_info=True)

    async def delete(self, key: str) -> None:
        client = self._get_client()
        if client is None:
            return
        try:
            await client.delete(key)
        except Exception:
            logger.debug("cache delete failed for %s", key, exc_info=True)

    async def namespace_version(self, namespace: str) -> int:
        client = self._get_client()
        if client is None:
            return 0
        try:
            raw = await client.get(self._version_key(namespace))
        except Exception:
            logger.debug("cache version read failed for %s", namespace, exc_info=True)
            return 0
        try:
            return int(raw) if raw is not None else 0
        except (TypeError, ValueError):
            return 0

    async def bump_namespace(self, namespace: str) -> None:
        client = self._get_client()
        if client is None:
            return
        key = self._version_key(namespace)
        try:
            # INCR is atomic: two replicas invalidating at once both move it
            # forward, and neither can resurrect a stale version.
            await client.incr(key)
            await client.expire(key, _VERSION_TTL_SECONDS)
        except Exception:
            logger.debug("cache bump failed for %s", namespace, exc_info=True)

    @staticmethod
    def _version_key(namespace: str) -> str:
        return f"ns:{namespace}"

    async def close(self) -> None:
        """Release the connection pool (called from the app lifespan)."""
        if self._client is not None:
            try:
                await self._client.aclose()
            except Exception:  # pragma: no cover - best effort on shutdown
                logger.debug("cache close failed", exc_info=True)
