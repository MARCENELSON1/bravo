"""Pantalla Finanzas Tanda F: capa de snapshots diarios (performance a escala).

Tabla ``finance_daily_snapshots`` (tenant_id + day + totales de ventas) con RLS.
Se mantiene incremental en el projector y se puede reconstruir; el read model del
Asesor la usa según flag (default: cálculo live).

Revision ID: 0019_finance_daily_snapshots
Revises: 0018_advisor_seats_hours
Create Date: 2026-07-04
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

from app.infrastructure.persistence.models import Base, FinanceDailySnapshotORM

revision: str = "0019_finance_daily_snapshots"
down_revision: str | None = "0018_advisor_seats_hours"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

APP_ROLE = "bravo_app"
RLS_TABLES = ("finance_daily_snapshots",)
_NEW_TABLES = [FinanceDailySnapshotORM.__table__]


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
    bind = op.get_bind()
    for table in RLS_TABLES:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table};")
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")
    Base.metadata.drop_all(bind=bind, tables=_NEW_TABLES)
