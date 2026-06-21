from __future__ import annotations

from sqlalchemy import select

from app.domain.inventory.entities import Ingredient
from app.domain.inventory.repository import IngredientRepository
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.mappers import ingredient_to_domain, ingredient_to_orm
from app.infrastructure.persistence.models import IngredientORM


class SqlAlchemyIngredientRepository(IngredientRepository):
    """Every query is scoped by ``tenant_id`` (defence in depth on top of RLS)."""

    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def get_by_id(self, tenant_id: str, ingredient_id: str) -> Ingredient | None:
        async with self._session_factory() as session:
            stmt = select(IngredientORM).where(
                IngredientORM.id == ingredient_id, IngredientORM.tenant_id == tenant_id
            )
            row = (await session.execute(stmt)).scalar_one_or_none()
            return ingredient_to_domain(row) if row is not None else None

    async def list_below_min(self, tenant_id: str) -> list[Ingredient]:
        async with self._session_factory() as session:
            stmt = (
                select(IngredientORM)
                .where(
                    IngredientORM.tenant_id == tenant_id,
                    IngredientORM.active.is_(True),
                    IngredientORM.stock_qty <= IngredientORM.min_qty,
                )
                .order_by(IngredientORM.name)
            )
            rows = (await session.execute(stmt)).scalars().all()
            return [ingredient_to_domain(row) for row in rows]

    async def list(self, tenant_id: str, *, active_only: bool = False) -> list[Ingredient]:
        async with self._session_factory() as session:
            stmt = select(IngredientORM).where(IngredientORM.tenant_id == tenant_id)
            if active_only:
                stmt = stmt.where(IngredientORM.active.is_(True))
            stmt = stmt.order_by(IngredientORM.name)
            rows = (await session.execute(stmt)).scalars().all()
            return [ingredient_to_domain(row) for row in rows]

    async def add(self, ingredient: Ingredient) -> None:
        async with self._session_factory() as session:
            session.add(ingredient_to_orm(ingredient))

    async def save(self, ingredient: Ingredient) -> None:
        async with self._session_factory() as session:
            await session.merge(ingredient_to_orm(ingredient))
