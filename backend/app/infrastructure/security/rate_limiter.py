from __future__ import annotations

import time
from collections import defaultdict
from collections.abc import Callable

from app.domain.shared.exceptions import RateLimited
from app.domain.shared.rate_limiter import RateLimiter


class InMemoryRateLimiter(RateLimiter):
    """In-process sliding-window rate limiter (no external deps). Keeps the recent
    hit timestamps per key and rejects the (limit+1)-th within the window.

    Scoped to one process: fine as an abuse guard on the public Carta QR endpoints
    (Railway runs a single API instance today). If the API is ever scaled out,
    swap this adapter for a shared (Redis) one behind the same port. ``check`` has
    no awaits between read and mutate, so it is atomic on the event loop (no lock)."""

    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        self._hits: dict[str, list[float]] = defaultdict(list)
        self._clock = clock

    async def check(self, key: str, *, limit: int, window_seconds: int) -> None:
        now = self._clock()
        cutoff = now - window_seconds
        recent = [t for t in self._hits[key] if t > cutoff]
        if len(recent) >= limit:
            self._hits[key] = recent  # keep it pruned even when rejecting
            raise RateLimited()
        recent.append(now)
        self._hits[key] = recent
