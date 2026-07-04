from __future__ import annotations

import json
from uuid import uuid4

from sqlalchemy import delete, select

from app.domain.advisor.ports import NarratedInsight
from app.domain.advisor.repository import AdvisorDiagnosticsCache, CachedDiagnostics
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.models import AdvisorDiagnosticsORM


def _to_payload(diagnostics: CachedDiagnostics) -> str:
    return json.dumps(
        {
            "insights": [
                {
                    "code": i.code,
                    "severity": i.severity,
                    "bucket": i.bucket,
                    "title": i.title,
                    "body": i.body,
                    "action": i.action,
                }
                for i in diagnostics.insights
            ],
            "summary": diagnostics.summary,
        }
    )


def _from_payload(row: AdvisorDiagnosticsORM) -> CachedDiagnostics:
    data = json.loads(row.payload)
    return CachedDiagnostics(
        insights=[NarratedInsight(**i) for i in data["insights"]],
        summary=data["summary"],
        generated_at=row.generated_at,
    )


class SqlAlchemyAdvisorDiagnosticsCache(AdvisorDiagnosticsCache):
    """Cada query scopeada por ``tenant_id`` (defensa en profundidad sobre RLS)."""

    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def get(self, tenant_id: str, fingerprint: str) -> CachedDiagnostics | None:
        async with self._session_factory() as session:
            stmt = select(AdvisorDiagnosticsORM).where(
                AdvisorDiagnosticsORM.tenant_id == tenant_id,
                AdvisorDiagnosticsORM.fingerprint == fingerprint,
            )
            row = (await session.execute(stmt)).scalar_one_or_none()
            return _from_payload(row) if row is not None else None

    async def put(
        self, tenant_id: str, fingerprint: str, diagnostics: CachedDiagnostics
    ) -> None:
        payload = _to_payload(diagnostics)
        async with self._session_factory() as session:
            stmt = select(AdvisorDiagnosticsORM).where(
                AdvisorDiagnosticsORM.tenant_id == tenant_id,
                AdvisorDiagnosticsORM.fingerprint == fingerprint,
            )
            existing = (await session.execute(stmt)).scalar_one_or_none()
            if existing is not None:
                existing.payload = payload
                existing.generated_at = diagnostics.generated_at
            else:
                session.add(
                    AdvisorDiagnosticsORM(
                        id=str(uuid4()),
                        tenant_id=tenant_id,
                        fingerprint=fingerprint,
                        payload=payload,
                        generated_at=diagnostics.generated_at,
                    )
                )

    async def purge(self, tenant_id: str) -> int:
        async with self._session_factory() as session:
            stmt = delete(AdvisorDiagnosticsORM).where(
                AdvisorDiagnosticsORM.tenant_id == tenant_id
            )
            result = await session.execute(stmt)
            return int(result.rowcount or 0)
