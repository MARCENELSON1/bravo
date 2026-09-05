from __future__ import annotations

from typing import Any

from app.domain.shared.cache import namespace_for
from app.infrastructure.cache.memory_cache import InMemoryCache
from app.infrastructure.cache.redis_cache import RedisCache


class _Clock:
    """Manual clock so TTL expiry is tested without sleeping."""

    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


async def test_hit_and_miss() -> None:
    cache = InMemoryCache()
    assert await cache.get("k") is None  # miss on an unknown key
    await cache.set("k", ["a"], ttl_seconds=60)
    assert await cache.get("k") == ["a"]


async def test_entry_expires_after_ttl() -> None:
    clock = _Clock()
    cache = InMemoryCache(clock=clock)
    await cache.set("k", "v", ttl_seconds=60)
    clock.now = 59.0
    assert await cache.get("k") == "v"
    clock.now = 61.0
    assert await cache.get("k") is None


async def test_delete_drops_the_key() -> None:
    cache = InMemoryCache()
    await cache.set("k", "v", ttl_seconds=60)
    await cache.delete("k")
    assert await cache.get("k") is None


async def test_bump_namespace_invalidates_by_version() -> None:
    # Invalidating moves the version forward, so keys built with the old version
    # become unreachable (they are never read again and expire on their own).
    cache = InMemoryCache()
    ns = namespace_for("products", "t-1")
    assert await cache.namespace_version(ns) == 0
    old_key = f"{ns}:v0:list"
    await cache.set(old_key, ["stale"], ttl_seconds=60)

    await cache.bump_namespace(ns)

    assert await cache.namespace_version(ns) == 1
    assert await cache.get(f"{ns}:v1:list") is None  # the new key is a clean miss


async def test_namespaces_are_isolated_per_tenant() -> None:
    cache = InMemoryCache()
    a, b = namespace_for("products", "t-a"), namespace_for("products", "t-b")
    await cache.bump_namespace(a)
    assert await cache.namespace_version(a) == 1
    assert await cache.namespace_version(b) == 0  # otro tenant no se ve afectado


async def test_lru_evicts_the_least_recently_used() -> None:
    cache = InMemoryCache(max_entries=2)
    await cache.set("a", 1, ttl_seconds=60)
    await cache.set("b", 2, ttl_seconds=60)
    await cache.get("a")  # touch "a" so "b" becomes the oldest
    await cache.set("c", 3, ttl_seconds=60)

    assert await cache.get("b") is None  # evicted
    assert await cache.get("a") == 1
    assert await cache.get("c") == 3


class _BrokenRedis:
    """Every operation blows up — stands in for an outage or a timeout."""

    async def get(self, *_: Any, **__: Any) -> Any:
        raise ConnectionError("redis down")

    async def set(self, *_: Any, **__: Any) -> Any:
        raise ConnectionError("redis down")

    async def delete(self, *_: Any, **__: Any) -> Any:
        raise ConnectionError("redis down")

    async def incr(self, *_: Any, **__: Any) -> Any:
        raise ConnectionError("redis down")

    async def expire(self, *_: Any, **__: Any) -> Any:
        raise ConnectionError("redis down")


async def test_redis_failure_degrades_to_a_miss_without_raising() -> None:
    # Fail-open: a cache outage must slow the system down, never break it.
    cache = RedisCache(url="redis://unused")
    cache._client = _BrokenRedis()

    await cache.set("k", "v", ttl_seconds=60)  # no raise
    assert await cache.get("k") is None  # behaves as a miss
    await cache.delete("k")  # no raise
    await cache.bump_namespace("products:t-1")  # no raise
    assert await cache.namespace_version("products:t-1") == 0


async def test_redis_roundtrip_with_a_fake_backend() -> None:
    class _FakeRedis:
        def __init__(self) -> None:
            self.store: dict[str, bytes] = {}

        async def get(self, key: str) -> bytes | None:
            return self.store.get(key)

        async def set(self, key: str, value: bytes, ex: int | None = None) -> None:
            self.store[key] = value

        async def incr(self, key: str) -> int:
            current = int(self.store.get(key, b"0"))
            self.store[key] = str(current + 1).encode()
            return current + 1

        async def expire(self, key: str, ttl: int) -> None:
            return None

    cache = RedisCache(url="redis://unused")
    cache._client = _FakeRedis()

    await cache.set("k", {"a": 1}, ttl_seconds=60)
    assert await cache.get("k") == {"a": 1}  # values survive the pickle round-trip
    await cache.bump_namespace("products:t-1")
    assert await cache.namespace_version("products:t-1") == 1
