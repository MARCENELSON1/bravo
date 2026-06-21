"""Fase 5: fichaje (shifts) + RLS + tenant standard_workday_minutes

Revision ID: 0006_shifts
Revises: 0005_invoices
Create Date: 2026-06-21
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op
from app.infrastructure.persistence.models import Base, ShiftORM

# revision identifiers, used by Alembic.
revision: str = "0006_shifts"
down_revision: str | None = "0005_invoices"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

APP_ROLE = "bravo_app"
RLS_TABLES = ("shifts",)
_NEW_TABLES = [ShiftORM.__table__]


def upgrade() -> None:
    bind = op.get_bind()
    op.add_column(
        "tenants",
        sa.Column(
            "standard_workday_minutes",
            sa.Integer(),
            server_default="480",
            nullable=False,
        ),
    )
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
    op.drop_column("tenants", "standard_workday_minutes")
