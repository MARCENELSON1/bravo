"""Fase 9.1: caché de diagnósticos del asesor — advisor_diagnostics + RLS

Tabla de caché de los textos narrados (insights + summary) por (tenant,
fingerprint de insights+proveedor), para no re-llamar al LLM en cada apertura
de la Pantalla Finanzas / Asesor. Datos de plata → RLS (mirror 0011).

Revision ID: 0015_advisor_diagnostics
Revises: 0014_payment_tip
Create Date: 2026-06-28
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
from app.infrastructure.persistence.models import AdvisorDiagnosticsORM, Base

# revision identifiers, used by Alembic.
revision: str = "0015_advisor_diagnostics"
down_revision: str | None = "0014_payment_tip"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

APP_ROLE = "bravo_app"
RLS_TABLES = ("advisor_diagnostics",)
_NEW_TABLES = [AdvisorDiagnosticsORM.__table__]


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
