"""Async database engine + session factory with per-transaction tenant scoping.

``Database.session()`` yields an :class:`AsyncSession` already inside a
transaction. When a tenant is present in the request context, the transaction is
scoped with ``SET LOCAL app.tenant_id`` (via ``set_config(..., true)``) so that
Postgres Row Level Security policies apply. The bound method is injected into
repositories as their ``session_factory``.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.context import get_current_tenant

# Repositories receive ``Database.session`` (bound method) as this callable.
SessionFactory = Callable[[], AbstractAsyncContextManager[AsyncSession]]


class Database:
    """Owns the async engine and produces tenant-scoped sessions.

    The pool is sized explicitly by the caller (wired from settings) instead of
    inheriting the driver default of 5 + 10: a process can hold at most
    ``pool_size + max_overflow`` connections, so that figure times the number of
    workers and replicas has to stay under the server's ``max_connections``.
    ``pool_timeout`` is kept short on purpose — a request that cannot get a
    connection should fail fast and visibly rather than hang.
    """

    def __init__(
        self,
        url: str,
        *,
        pool_size: int = 10,
        max_overflow: int = 20,
        pool_timeout: int = 10,
        pool_recycle: int = 1800,
    ) -> None:
        self._engine = create_async_engine(
            url,
            pool_pre_ping=True,
            future=True,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
            pool_recycle=pool_recycle,
        )
        self._sessionmaker = async_sessionmaker(self._engine, expire_on_commit=False)

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        async with self._sessionmaker() as session:
            async with session.begin():
                tenant_id = get_current_tenant()
                if tenant_id is not None:
                    # set_config(..., is_local=true) keeps the setting bound to
                    # this transaction only; bind parameters avoid SQL injection
                    # (plain ``SET LOCAL`` does not accept bind parameters).
                    await session.execute(
                        text("SELECT set_config('app.tenant_id', :tenant_id, true)"),
                        {"tenant_id": str(tenant_id)},
                    )
                yield session

    async def dispose(self) -> None:
        await self._engine.dispose()
