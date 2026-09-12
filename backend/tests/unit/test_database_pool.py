"""The connection pool is sized on purpose, not left at the driver default.

A process can hold at most ``pool_size + max_overflow`` connections; once that
is exhausted every further request queues for ``pool_timeout`` seconds. Leaving
those at the defaults (5 + 10, waiting 30s) put a hard ceiling on concurrency
that nobody had chosen.
"""

from __future__ import annotations

from app.infrastructure.persistence.database import Database

_URL = "postgresql+asyncpg://user:pw@localhost:5432/nowhere"


def test_pool_is_sized_from_the_given_settings():
    db = Database(_URL, pool_size=7, max_overflow=13, pool_timeout=3, pool_recycle=900)
    pool = db._engine.pool

    assert pool.size() == 7
    assert pool._max_overflow == 13
    assert pool._timeout == 3
    assert pool._recycle == 900


def test_defaults_are_wider_than_the_driver_defaults():
    # Guards the regression: SQLAlchemy would otherwise cap a process at 5 + 10.
    db = Database(_URL)
    pool = db._engine.pool

    assert pool.size() > 5
    assert pool._max_overflow > 10
    # Fail fast instead of hanging a request for the default 30 seconds.
    assert pool._timeout < 30


def test_pre_ping_stays_enabled():
    # Managed Postgres drops idle connections; without pre-ping the first query
    # after that surfaces as a spurious error to the user.
    db = Database(_URL)
    assert db._engine.pool._pre_ping is True
