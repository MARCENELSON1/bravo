from __future__ import annotations

import logging
import pickle
from typing import Any

from app.domain.shared.cache import CachePort
from app.infrastructure.redis.connection import RedisProvider

logger = logging.getLogger(__name__)

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

    The connection is owned by :class:`RedisProvider` and shared with the event
    bus and the rate limiter; closing it is the lifespan's job, not this class's.

    **Fail-open by design**: every operation swallows backend errors and
    timeouts, logging at debug level. A Redis outage degrades the system to
    "always miss" (slower, still correct) instead of taking it down.
    """

    def __init__(self, redis: RedisProvider) -> None:
        self._redis = redis

    def _get_client(self) -> Any | None:
        """The process-wide client (short read timeout), or ``None`` if Redis is
        unusable — in which case every operation degrades to a miss."""
        return self._redis.client()

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
