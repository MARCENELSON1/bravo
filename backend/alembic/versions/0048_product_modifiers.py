"""product modifiers (Carta QR F2 D): modifier groups + options + order snapshot.

Two new RLS tables — ``product_modifier_groups`` and ``product_modifier_options``
— let a product carry choices the diner picks from (ej. "Punto de cocción",
"+Panceta"), with min/max rules and a per-option ``price_delta``. Plus an additive
JSON column ``order_items.selected_options`` snapshotting the choices made on a
line (display-only; the delta is already folded into ``unit_price_amount``). All
additive/nullable → every existing product/order behaves exactly as before.

Revision ID: 0048_product_modifiers
Revises: 0047_self_order
Create Date: 2026-09-01
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op
from app.infrastructure.persistence.models import (
    Base,
    ProductModifierGroupORM,
    ProductModifierOptionORM,
)

revision: str = "0048_product_modifiers"
down_revision: str | None = "0047_self_order"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

APP_ROLE = "bravo_app"
RLS_TABLES = ("product_modifier_groups", "product_modifier_options")
_NEW_TABLES = [ProductModifierGroupORM.__table__, ProductModifierOptionORM.__table__]


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
    op.add_column(
        "order_items",
        sa.Column("selected_options", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("order_items", "selected_options")
    bind = op.get_bind()
    for table in RLS_TABLES:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table};")
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")
    Base.metadata.drop_all(bind=bind, tables=_NEW_TABLES)
