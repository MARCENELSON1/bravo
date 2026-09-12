from __future__ import annotations

from abc import ABC, abstractmethod


class RateLimiter(ABC):
    """Port for a per-key rate limit. Guards unauthenticated, abuse-prone actions
    (the public Carta QR endpoints, scoped only by the table token): too many hits
    on the same key inside the window raise ``RateLimited``."""

    @abstractmethod
    async def check(self, key: str, *, limit: int, window_seconds: int) -> None:
        """Record one hit for ``key`` and raise ``RateLimited`` if it is the
        (limit+1)-th within the trailing ``window_seconds``."""
