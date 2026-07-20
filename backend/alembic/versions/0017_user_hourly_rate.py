"""Pantalla Finanzas Tanda D: valor/hora por empleado para el labor cost real.

``users.hourly_rate_amount`` (unidad mínima, moneda del tenant) — columna
additiva y opcional: sin rate, el labor sigue cayendo al costo mensual
configurado en el Asesor (prorrateado).

Revision ID: 0017_user_hourly_rate
Revises: 0016_user_name
Create Date: 2026-07-04
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0017_user_hourly_rate"
down_revision: str | None = "0016_user_name"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users", sa.Column("hourly_rate_amount", sa.BigInteger(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("users", "hourly_rate_amount")
