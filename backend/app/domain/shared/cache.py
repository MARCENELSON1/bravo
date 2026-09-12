from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

# Catalog entries change rarely but are read on every hot request, so they are
# cached with a short TTL as a backstop. Reads must never serve a stale price
# after an edit, hence the namespace-versioning scheme below.
CATALOG_TTL_SECONDS = 60


class CachePort(ABC):
    """Port for a key/value cache with namespace invalidation.

    **Why namespace versioning.** Neither Redis nor Memcached can delete by
    pattern, so "drop everything cached for tenant X" is impossible to express
    directly. Instead every namespace (``tenant_id`` + entity, e.g.
    ``"products:t-1"``) carries a monotonically increasing version, and the
    version is baked into each key::

        products:t-1:v7:list:only_active=True

    Invalidating is then a single ``bump_namespace`` that moves the version to
    ``v8``: the ``v7`` keys become unreachable and expire on their own TTL. That
    makes invalidation O(1) and atomic, at the cost of leaving orphan keys
    behind for at most one TTL.

    Implementations must be **fail-open**: a cache backend that is down or slow
    degrades to a miss (the caller falls back to the database) and never raises
    into the request path.
    """

    @abstractmethod
    async def get(self, key: str) -> Any | None:
        """Cached value, or ``None`` on miss (including any backend failure)."""
        ...

    @abstractmethod
    async def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        """Store ``value`` under ``key`` for ``ttl_seconds``. Never raises."""
        ...

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Drop a single key. Never raises."""
        ...

    @abstractmethod
    async def namespace_version(self, namespace: str) -> int:
        """Current version of ``namespace`` (starts at 0)."""
        ...

    @abstractmethod
    async def bump_namespace(self, namespace: str) -> None:
        """Invalidate every key of ``namespace`` by moving its version forward."""
        ...


def namespace_for(entity: str, tenant_id: str) -> str:
    """Cache namespace of one entity within one tenant — the invalidation unit.

    Keeping ``tenant_id`` in the namespace means a write by one tenant can never
    invalidate (nor expose) another tenant's cached catalog.
    """
    return f"{entity}:{tenant_id}"
