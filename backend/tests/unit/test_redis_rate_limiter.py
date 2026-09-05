"""The shared rate limiter: one limit across replicas, not one per replica.

Honest scope: no Redis server (and no Lua runtime) is available in this suite, so
``_FakeScript`` below *mirrors* the sliding-window script rather than running it.
That still tests what the adapter is responsible for — namespacing, the arguments
it passes, raising on rejection, failing open, and above all sharing one counter
between two instances — but the Lua text itself is only truly exercised against a
real server. Treat a change to ``_SLIDING_WINDOW_LUA`` as untested by this file.
"""

from __future__ import annotations

import pytest

from app.domain.shared.exceptions import RateLimited
from app.infrastructure.security.redis_rate_limiter import RedisRateLimiter


class _Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


class _FakeScript:
    """Mirrors _SLIDING_WINDOW_LUA against a dict of sorted sets."""

    def __init__(self, store: dict[str, list[tuple[float, str]]]) -> None:
        self.store = store
        self.calls: list[dict[str, object]] = []

    async def __call__(self, keys: list[str], args: list[object]) -> int:
        now, window, limit, member = (
            float(args[0]),
            float(args[1]),
            int(args[2]),
            str(args[3]),
        )
        self.calls.append({"key": keys[0], "now": now, "member": member})
        entries = [e for e in self.store.get(keys[0], []) if e[0] > now - window]
        if len(entries) >= limit:
            self.store[keys[0]] = entries
            return 0
        entries.append((now, member))
        self.store[keys[0]] = entries
        return 1


class _FakeRedis:
    def __init__(self, store: dict[str, list[tuple[float, str]]]) -> None:
        self.store = store
        self.scripts: list[_FakeScript] = []

    def register_script(self, source: str) -> _FakeScript:
        created = _FakeScript(self.store)
        self.scripts.append(created)
        return created


class _FakeProvider:
    """One Redis, however many limiters — i.e. however many replicas."""

    def __init__(self, store: dict[str, list[tuple[float, str]]]) -> None:
        self.redis = _FakeRedis(store)

    def client(self):  # noqa: ANN201
        return self.redis


class _BrokenProvider:
    def client(self):  # noqa: ANN201
        raise RuntimeError("redis is down")


class _NoRedisProvider:
    def client(self):  # noqa: ANN201
        return None


def _limiter(store, clock=None) -> RedisRateLimiter:  # noqa: ANN001
    return RedisRateLimiter(_FakeProvider(store), clock=clock or _Clock())


async def test_allows_up_to_the_limit_then_blocks() -> None:
    limiter = _limiter({})

    for _ in range(3):
        await limiter.check("k", limit=3, window_seconds=60)
    with pytest.raises(RateLimited):
        await limiter.check("k", limit=3, window_seconds=60)


async def test_two_replicas_enforce_one_shared_limit() -> None:
    # The reason this adapter exists. With the in-memory limiter, N replicas mean
    # N separate counters and an attacker gets N times the allowance.
    store: dict[str, list[tuple[float, str]]] = {}
    clock = _Clock()
    replica_a = RedisRateLimiter(_FakeProvider(store), clock=clock)
    replica_b = RedisRateLimiter(_FakeProvider(store), clock=clock)

    await replica_a.check("k", limit=2, window_seconds=60)
    await replica_b.check("k", limit=2, window_seconds=60)
    # The third hit is rejected no matter which replica it lands on.
    with pytest.raises(RateLimited):
        await replica_a.check("k", limit=2, window_seconds=60)
    with pytest.raises(RateLimited):
        await replica_b.check("k", limit=2, window_seconds=60)


async def test_window_slides_so_old_hits_expire() -> None:
    clock = _Clock()
    limiter = _limiter({}, clock)

    for _ in range(3):
        await limiter.check("k", limit=3, window_seconds=60)
    clock.now += 61
    await limiter.check("k", limit=3, window_seconds=60)


async def test_keys_are_independent() -> None:
    limiter = _limiter({})

    await limiter.check("a", limit=1, window_seconds=60)
    await limiter.check("b", limit=1, window_seconds=60)
    with pytest.raises(RateLimited):
        await limiter.check("a", limit=1, window_seconds=60)


async def test_hits_in_the_same_instant_all_count() -> None:
    # A frozen clock is the adversarial case: without a unique member per hit,
    # ZADD would overwrite the same score and the limit would never be reached.
    limiter = _limiter({}, _Clock())

    for _ in range(2):
        await limiter.check("k", limit=2, window_seconds=60)
    with pytest.raises(RateLimited):
        await limiter.check("k", limit=2, window_seconds=60)


async def test_keys_are_namespaced_away_from_cache_entries() -> None:
    provider = _FakeProvider({})
    limiter = RedisRateLimiter(provider, clock=_Clock())

    await limiter.check("qr:menu:t1", limit=5, window_seconds=60)

    assert provider.redis.scripts[0].calls[0]["key"] == "rl:qr:menu:t1"


async def test_script_is_registered_once_and_reused() -> None:
    # Re-registering per call would add a round trip to every public request.
    provider = _FakeProvider({})
    limiter = RedisRateLimiter(provider, clock=_Clock())

    for _ in range(3):
        await limiter.check("k", limit=10, window_seconds=60)

    assert len(provider.redis.scripts) == 1


async def test_redis_down_lets_the_request_through() -> None:
    # Deliberate: this guards public QR endpoints against abuse, it is not an
    # authorization check. A Redis outage must not close the restaurant.
    limiter = RedisRateLimiter(_BrokenProvider(), clock=_Clock())
    await limiter.check("k", limit=1, window_seconds=60)
    await limiter.check("k", limit=1, window_seconds=60)


async def test_no_backend_configured_lets_the_request_through() -> None:
    limiter = RedisRateLimiter(_NoRedisProvider(), clock=_Clock())
    await limiter.check("k", limit=1, window_seconds=60)
