"""Productos v2 Tanda C: recetas madre / preparaciones anidadas.

Tablas nuevas ``preparations`` + ``preparation_items`` (RLS) y, en
``recipe_items``, columna aditiva ``preparation_id`` + ``ingredient_id`` pasa a
ser nullable (un ítem es un insumo O una preparación).

Revision ID: 0021_preparations
Revises: 0020_product_pricing
Create Date: 2026-08-02
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op
from app.infrastructure.persistence.models import (
    Base,
    PreparationItemORM,
    PreparationORM,
)

revision: str = "0021_preparations"
down_revision: str | None = "0020_product_pricing"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

APP_ROLE = "bravo_app"
RLS_TABLES = ("preparations", "preparation_items")
_NEW_TABLES = [PreparationORM.__table__, PreparationItemORM.__table__]


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
        "recipe_items",
        sa.Column("preparation_id", sa.Uuid(as_uuid=False), nullable=True),
    )
    op.create_index(
        "ix_recipe_items_preparation_id", "recipe_items", ["preparation_id"]
    )
    op.alter_column("recipe_items", "ingredient_id", nullable=True)


def downgrade() -> None:
    op.alter_column("recipe_items", "ingredient_id", nullable=False)
    op.drop_index("ix_recipe_items_preparation_id", table_name="recipe_items")
    op.drop_column("recipe_items", "preparation_id")
    bind = op.get_bind()
    for table in RLS_TABLES:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {table};")
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")
    Base.metadata.drop_all(bind=bind, tables=_NEW_TABLES)
