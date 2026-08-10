"""add recipe versioning (Fase 2D).

Incremental ``recipes.version`` (bumped on every SetRecipe) + a per-sale snapshot
``sale_facts.recipe_version`` for attribution — the food cost itself is already
frozen per sale. Existing recipes backfill to v1; existing sale_facts rows stay
NULL (no version recorded).
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0027_recipe_version"
down_revision: str | None = "0026_recipe_unit"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "recipes",
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column(
        "sale_facts",
        sa.Column("recipe_version", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("sale_facts", "recipe_version")
    op.drop_column("recipes", "version")
