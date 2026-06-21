from __future__ import annotations

from uuid import uuid4

from sqlalchemy import delete, select

from app.domain.inventory.recipe import Recipe
from app.domain.inventory.repository import RecipeRepository
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.mappers import (
    recipe_item_to_orm,
    recipe_to_domain,
    recipe_to_orm,
)
from app.infrastructure.persistence.models import RecipeItemORM, RecipeORM


class SqlAlchemyRecipeRepository(RecipeRepository):
    """A recipe is keyed by ``product_id`` (1:1). Items have no domain identity,
    so ``save`` replaces the whole set. Every query is scoped by ``tenant_id``."""

    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def get_for_product(self, tenant_id: str, product_id: str) -> Recipe | None:
        async with self._session_factory() as session:
            recipe_row = (
                await session.execute(
                    select(RecipeORM).where(
                        RecipeORM.product_id == product_id,
                        RecipeORM.tenant_id == tenant_id,
                    )
                )
            ).scalar_one_or_none()
            if recipe_row is None:
                return None
            item_rows = (
                await session.execute(
                    select(RecipeItemORM).where(
                        RecipeItemORM.product_id == product_id,
                        RecipeItemORM.tenant_id == tenant_id,
                    )
                )
            ).scalars().all()
            return recipe_to_domain(recipe_row, list(item_rows))

    async def list_for_products(
        self, tenant_id: str, product_ids: list[str]
    ) -> dict[str, Recipe]:
        if not product_ids:
            return {}
        async with self._session_factory() as session:
            recipe_rows = (
                await session.execute(
                    select(RecipeORM).where(
                        RecipeORM.tenant_id == tenant_id,
                        RecipeORM.product_id.in_(product_ids),
                    )
                )
            ).scalars().all()
            if not recipe_rows:
                return {}
            item_rows = (
                await session.execute(
                    select(RecipeItemORM).where(
                        RecipeItemORM.tenant_id == tenant_id,
                        RecipeItemORM.product_id.in_(product_ids),
                    )
                )
            ).scalars().all()
            items_by_product: dict[str, list[RecipeItemORM]] = {}
            for item in item_rows:
                items_by_product.setdefault(item.product_id, []).append(item)
            return {
                row.product_id: recipe_to_domain(
                    row, items_by_product.get(row.product_id, [])
                )
                for row in recipe_rows
            }

    async def save(self, recipe: Recipe) -> None:
        async with self._session_factory() as session:
            await session.merge(recipe_to_orm(recipe))
            await session.execute(
                delete(RecipeItemORM).where(
                    RecipeItemORM.product_id == recipe.product_id,
                    RecipeItemORM.tenant_id == recipe.tenant_id,
                )
            )
            for item in recipe.items:
                session.add(recipe_item_to_orm(item, recipe, str(uuid4())))
