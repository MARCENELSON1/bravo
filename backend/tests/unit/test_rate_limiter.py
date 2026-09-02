"""Unit tests for the in-memory sliding-window rate limiter (Carta QR public
endpoints abuse guard)."""

from __future__ import annotations

import pytest

from app.domain.shared.exceptions import RateLimited
from app.infrastructure.security.rate_limiter import InMemoryRateLimiter


class _Clock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


async def test_allows_up_to_the_limit_then_blocks() -> None:
    clock = _Clock()
    limiter = InMemoryRateLimiter(clock=clock)

    for _ in range(3):  # the first `limit` hits pass
        await limiter.check("k", limit=3, window_seconds=60)
    with pytest.raises(RateLimited):  # the (limit+1)-th is rejected
        await limiter.check("k", limit=3, window_seconds=60)


async def test_window_slides_so_old_hits_expire() -> None:
    clock = _Clock()
    limiter = InMemoryRateLimiter(clock=clock)

    for _ in range(3):
        await limiter.check("k", limit=3, window_seconds=60)
    clock.now += 61  # everything falls out of the trailing window
    await limiter.check("k", limit=3, window_seconds=60)  # allowed again


async def test_keys_are_independent() -> None:
    limiter = InMemoryRateLimiter(clock=_Clock())

    await limiter.check("a", limit=1, window_seconds=60)
    # A different key is untouched by 'a' hitting its limit.
    await limiter.check("b", limit=1, window_seconds=60)
    with pytest.raises(RateLimited):
        await limiter.check("a", limit=1, window_seconds=60)
