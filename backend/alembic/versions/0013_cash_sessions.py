"""Fase 14 Tanda E: cash_sessions + cash_counts (arqueo Z) + RLS

New tenant-scoped tables for the register turn (caja) and its per-method count.
Both get FORCE RLS + the tenant_isolation policy (datos de plata), mirroring 0010.

Revision ID: 0013_cash_sessions
Revises: 0012_item_lifecycle_station
Create Date: 2026-06-28
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
from app.infrastructure.persistence.models import Base, CashCountORM, CashSessionORM

# revision identifiers, used by Alembic.
revision: str = "0013_cash_sessions"
down_revision: str | None = "0012_item_lifecycle_station"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

APP_ROLE = "bravo_app"
RLS_TABLES = ("cash_sessions", "cash_counts")
_NEW_TABLES = [CashSessionORM.__table__, CashCountORM.__table__]


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind, tables=_NEW_TABLES)
    op.execute(
        f"GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {APP_ROLE};"
    )
    for table in RLS_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;")
        op.execute(
            f"""
            CREATE POLICY tenant_isolation ON {table}
                USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
                WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
            """
        )


def downgrade() -> None:
    for table in RLS_TABLES:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table};")
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind, tables=_NEW_TABLES)
