"""Push (Fase 4): tabla ``device_tokens`` por tenant/usuario, con RLS.

Guarda el FCM token de cada device de un usuario (para mandarle push cuando su
comanda queda lista o le asignan una mesa, con la app cerrada). Tenant-scoped +
RLS (red de seguridad multi-tenant). ``token`` único → upsert por device.

Revision ID: 0053_device_tokens
Revises: 0052_widen_order_source
Create Date: 2026-09-03
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
from app.infrastructure.persistence.models import Base, DeviceTokenORM

revision: str = "0053_device_tokens"
down_revision: str | None = "0052_widen_order_source"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

APP_ROLE = "bravo_app"
RLS_TABLES = ("device_tokens",)
_NEW_TABLES = [DeviceTokenORM.__table__]


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
