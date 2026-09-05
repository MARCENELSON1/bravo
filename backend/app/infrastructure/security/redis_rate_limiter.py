from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Callable
from typing import Any

from app.domain.shared.exceptions import RateLimited
from app.domain.shared.rate_limiter import RateLimiter
from app.infrastructure.redis.connection import RedisProvider

logger = logging.getLogger(__name__)

# One sorted set per key, holding the timestamps of the recent hits. Read-then-
# write from Python would race across replicas (two could each see limit-1 and
# both allow), which is exactly the bug this adapter exists to fix — so the whole
# decision runs server-side, where it is atomic.
_SLIDING_WINDOW_LUA = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])
local member = ARGV[4]
redis.call('ZREMRANGEBYSCORE', key, '-inf', now - window)
local used = redis.call('ZCARD', key)
if used >= limit then
  redis.call('EXPIRE', key, window + 1)
  return 0
end
redis.call('ZADD', key, now, member)
redis.call('EXPIRE', key, window + 1)
return 1
"""


class RedisRateLimiter(RateLimiter):
    """Sliding-window rate limiter shared across replicas.

    Same semantics as :class:`InMemoryRateLimiter` — the (limit+1)-th hit inside
    the window is rejected, and a rejected hit is not recorded — but the counter
    lives in Redis, so N replicas enforce one limit instead of N.

    **Fail-open on purpose**: if Redis is unreachable the request is allowed.
    This is an abuse guard on the public QR endpoints, not an authorization
    check; turning a backend outage into "nobody can order" would do more damage
    than the abuse it prevents. Authorization never depends on this class.
    """

    def __init__(
        self,
        redis: RedisProvider,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self._redis = redis
        self._clock = clock
        self._script: Any | None = None

    async def check(self, key: str, *, limit: int, window_seconds: int) -> None:
        try:
            client = self._redis.client()
            if client is None:
                return  # fail-open: no backend, no guard
            if self._script is None:
                self._script = client.register_script(_SLIDING_WINDOW_LUA)
            allowed = await self._script(
                keys=[self._redis_key(key)],
                # A unique member per hit: two hits in the same millisecond must
                # both count, and ZADD would otherwise treat them as one.
                args=[self._clock(), window_seconds, limit, uuid.uuid4().hex],
            )
        except Exception:
            logger.debug("rate limit check failed for %s", key, exc_info=True)
            return  # fail-open
        if not int(allowed):
            raise RateLimited()

    @staticmethod
    def _redis_key(key: str) -> str:
        return f"rl:{key}"
