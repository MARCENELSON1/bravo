"""add ingredients.recipe_unit (Fase 2C — conversión de unidades).

Optional finer same-family sub-unit a recipe quantity is expressed in (KG→G,
L→ML). NULL = the recipe uses the ingredient's base unit (parity with today);
existing rows stay NULL so current recipes are untouched.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0026_recipe_unit"
down_revision: str | None = "0025_food_cost_net"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "ingredients",
        sa.Column("recipe_unit", sa.String(10), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("ingredients", "recipe_unit")
