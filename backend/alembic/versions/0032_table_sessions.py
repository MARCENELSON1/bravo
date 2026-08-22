"""table_sessions foundation (cimiento — la sesión de mesa como unidad de negocio).

Tablas nuevas ``sectors`` + ``table_sessions`` (RLS). Columnas aditivas
``tables.sector_id``/``capacity`` y ``orders.session_id`` (todo nullable). Backfill
1:1: cada orden ACTIVA (no PAID/CANCELLED) obtiene una ``table_session``
(``opened_at = order.created_at``, mismo mozo) y se cuelga vía ``session_id``. Las
órdenes cerradas quedan NULL (no se reconstruye historia). Todo nullable → paridad.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op
from app.infrastructure.persistence.models import Base, SectorORM, TableSessionORM

revision: str = "0032_table_sessions"
down_revision: str | None = "0031_payment_fees"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

APP_ROLE = "bravo_app"
RLS_TABLES = ("sectors", "table_sessions")
_NEW_TABLES = [SectorORM.__table__, TableSessionORM.__table__]


def upgrade() -> None:
    bind = op.get_bind()
    op.add_column("tables", sa.Column("sector_id", sa.Uuid(as_uuid=False), nullable=True))
    op.add_column("tables", sa.Column("capacity", sa.Integer(), nullable=True))
    op.create_index("ix_tables_sector_id", "tables", ["sector_id"])
    op.add_column("orders", sa.Column("session_id", sa.Uuid(as_uuid=False), nullable=True))
    op.create_index("ix_orders_session_id", "orders", ["session_id"])
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
    # Backfill 1:1 (idempotente): (1) cada orden activa recibe un session_id
    # generado; (2) se crea la sesión con esa PK. El link order.session_id = session.id
    # queda exacto, sin ambigüedad de matcheo.
    op.execute(
        """
        UPDATE orders SET session_id = gen_random_uuid()
        WHERE status NOT IN ('PAID','CANCELLED') AND session_id IS NULL
        """
    )
    op.execute(
        """
        INSERT INTO table_sessions
            (id, tenant_id, table_id, status, origin, waiter_id, opened_at, created_at)
        SELECT o.session_id, o.tenant_id, o.table_id, 'OPEN', 'SALON',
               o.waiter_id, o.created_at, now()
        FROM orders o
        WHERE o.session_id IS NOT NULL
          AND NOT EXISTS (SELECT 1 FROM table_sessions s WHERE s.id = o.session_id)
        """
    )


def downgrade() -> None:
    bind = op.get_bind()
    op.drop_index("ix_orders_session_id", table_name="orders")
    op.drop_column("orders", "session_id")
    op.drop_index("ix_tables_sector_id", table_name="tables")
    op.drop_column("tables", "capacity")
    op.drop_column("tables", "sector_id")
    for table in RLS_TABLES:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table};")
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")
    Base.metadata.drop_all(bind=bind, tables=_NEW_TABLES)
