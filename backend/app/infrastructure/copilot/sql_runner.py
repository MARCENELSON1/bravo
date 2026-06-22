"""Executes an already-VALIDATED SQL with defence in depth: a read-only
transaction + statement timeout, scoped to the tenant via RLS (``app.tenant_id``
is set by the session factory from the request context). Even if validation
missed a write, the read-only transaction blocks it; even if the SQL omits a
tenant filter, RLS only returns the tenant's rows."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import text

from app.domain.copilot.exceptions import CopilotQueryError
from app.domain.copilot.ports import CopilotQueryRunner, QueryResult
from app.infrastructure.persistence.database import SessionFactory


def _jsonable(value: object) -> object:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    if isinstance(value, UUID):
        return str(value)
    return str(value)


class SqlAlchemyCopilotQueryRunner(CopilotQueryRunner):
    def __init__(self, session_factory: SessionFactory, statement_timeout_ms: int) -> None:
        self._session_factory = session_factory
        self._timeout_ms = statement_timeout_ms

    async def run(self, tenant_id: str, sql: str) -> QueryResult:
        try:
            async with self._session_factory() as session:
                # set_config(..., is_local=true) = SET LOCAL (SET doesn't take binds).
                await session.execute(
                    text("SELECT set_config('statement_timeout', :ms, true)"),
                    {"ms": str(self._timeout_ms)},
                )
                await session.execute(
                    text("SELECT set_config('transaction_read_only', 'on', true)")
                )
                result = await session.execute(text(sql))
                columns = list(result.keys())
                rows = [[_jsonable(v) for v in row] for row in result.all()]
                return QueryResult(columns=columns, rows=rows)
        except Exception as exc:  # noqa: BLE001 — surface as a clean domain error
            raise CopilotQueryError() from exc
