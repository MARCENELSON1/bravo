"""Escalabilidad Fase 4: outbox genérico de trabajo diferido.

Tabla ``outbox_tasks``: una fila por trabajo que se saca del camino del usuario
(push de "curso listo", efectos de venta al cobrar, reporte de sales tax). Se
escribe con la misma DB que el cambio de negocio, así que sobrevive a un
reinicio, y un drainer la recorre con ``FOR UPDATE SKIP LOCKED``.

RLS como en el resto: el drainer NO puede leer la cola en global (la policy
esconde todo sin ``app.tenant_id``); recorre ``tenants`` y drena cada uno en su
propia transacción scopeada. Deliberadamente sin bypass.

Revision ID: 0056_outbox_tasks
Revises: 0055_hot_path_indexes
Create Date: 2026-09-05
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
from app.infrastructure.persistence.models import Base, OutboxTaskORM

revision: str = "0056_outbox_tasks"
down_revision: str | None = "0055_hot_path_indexes"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

APP_ROLE = "bravo_app"
RLS_TABLES = ("outbox_tasks",)
_NEW_TABLES = [OutboxTaskORM.__table__]


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
