"""proveedores enriquecidos: contacto + link de compras.

Agrega ``suppliers.phone`` + ``suppliers.notes`` y ``stock_movements.supplier_id``
(todo nullable → paridad). Permite contactar al proveedor (wa.me) y saber qué le
comprás a cada uno.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0038_supplier_enrichment"
down_revision: str | None = "0037_contact_log"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("suppliers", sa.Column("phone", sa.String(length=32), nullable=True))
    op.add_column("suppliers", sa.Column("notes", sa.String(length=500), nullable=True))
    op.add_column(
        "stock_movements",
        sa.Column("supplier_id", sa.Uuid(as_uuid=False), nullable=True),
    )
    op.create_index(
        "ix_stock_movements_supplier_id", "stock_movements", ["supplier_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_stock_movements_supplier_id", table_name="stock_movements")
    op.drop_column("stock_movements", "supplier_id")
    op.drop_column("suppliers", "notes")
    op.drop_column("suppliers", "phone")
