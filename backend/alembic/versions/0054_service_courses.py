"""Tiempos de servicio (coursing): ``course`` en productos y en líneas de comanda.

El curso es del PLATO (entrada / principal / postre / inmediato), se define una
vez en la carta y se copia a cada línea. La cocina cocina un curso a la vez y
el mozo dispara el siguiente ("marchar principales"). Se rellena lo existente
con un default razonable: barra → inmediato; categoría "entrada*" → entrada;
"postre*"/"dulce*" → postre; el resto → principal. Reversible sin pérdida de
datos operativos (solo se pierde la clasificación).

Revision ID: 0054_service_courses
Revises: 0053_device_tokens
Create Date: 2026-09-05
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0054_service_courses"
down_revision: str | None = "0053_device_tokens"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "products",
        sa.Column("course", sa.String(length=10), server_default="MAIN", nullable=False),
    )
    op.add_column(
        "order_items",
        sa.Column("course", sa.String(length=10), server_default="MAIN", nullable=False),
    )
    # Defaults inteligentes para lo que ya existe (idempotente).
    op.execute("UPDATE products SET course = 'IMMEDIATE' WHERE station = 'BAR'")
    op.execute(
        "UPDATE products SET course = 'STARTER' "
        "WHERE station = 'KITCHEN' AND lower(coalesce(category, '')) LIKE 'entrada%'"
    )
    op.execute(
        "UPDATE products SET course = 'DESSERT' "
        "WHERE station = 'KITCHEN' AND ("
        "lower(coalesce(category, '')) LIKE 'postre%' "
        "OR lower(coalesce(category, '')) LIKE 'dulce%')"
    )
    # Las líneas históricas heredan el curso de su producto (o inmediato si barra).
    op.execute(
        "UPDATE order_items oi SET course = p.course "
        "FROM products p WHERE p.id = oi.product_id"
    )
    op.execute("UPDATE order_items SET course = 'IMMEDIATE' WHERE station = 'BAR'")


def downgrade() -> None:
    op.drop_column("order_items", "course")
    op.drop_column("products", "course")
