from __future__ import annotations

import time
from collections import OrderedDict
from collections.abc import Callable
from typing import Any

from app.domain.shared.cache import CachePort

# Bounded so a long-running process with many tenants cannot grow without end.
# Catalog entries are small (a full menu is ~100 KB), so this is generous.
_DEFAULT_MAX_ENTRIES = 2048


class InMemoryCache(CachePort):
    """In-process LRU cache with per-entry TTL (the default backend).

    Fastest option (no serialization, no network) and enough for a single
    instance, which is how the API runs today. It is **per process**, so with
    several replicas each one keeps its own copy: a write invalidates only the
    replica that served it, and the others catch up when the TTL expires. Swap
    in :class:`RedisCache` to make invalidation instant across replicas.

    Eviction is LRU on insert; expired entries are dropped lazily on read.
    """

    def __init__(
        self,
        max_entries: int = _DEFAULT_MAX_ENTRIES,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._entries: OrderedDict[str, tuple[float, Any]] = OrderedDict()
        self._versions: dict[str, int] = {}
        self._max_entries = max_entries
        self._clock = clock

    async def get(self, key: str) -> Any | None:
        entry = self._entries.get(key)
        if entry is None:
            return None
        expires_at, value = entry
        if expires_at <= self._clock():
            del self._entries[key]  # lazily evict what already expired
            return None
        self._entries.move_to_end(key)  # touch: most recently used
        return value

    async def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        self._entries[key] = (self._clock() + ttl_seconds, value)
        self._entries.move_to_end(key)
        while len(self._entries) > self._max_entries:
            self._entries.popitem(last=False)  # drop the least recently used

    async def delete(self, key: str) -> None:
        self._entries.pop(key, None)

    async def namespace_version(self, namespace: str) -> int:
        return self._versions.get(namespace, 0)

    async def bump_namespace(self, namespace: str) -> None:
        self._versions[namespace] = self._versions.get(namespace, 0) + 1
