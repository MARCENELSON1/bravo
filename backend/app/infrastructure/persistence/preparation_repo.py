from __future__ import annotations

from uuid import uuid4

from sqlalchemy import delete, func, select

from app.domain.inventory.recipe import Preparation
from app.domain.inventory.repository import PreparationRepository
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.mappers import (
    preparation_item_to_orm,
    preparation_to_domain,
    preparation_to_orm,
)
from app.infrastructure.persistence.models import (
    PreparationItemORM,
    PreparationORM,
    RecipeItemORM,
)


class SqlAlchemyPreparationRepository(PreparationRepository):
    """Preparaciones (recetas madre). Los ítems no tienen identidad de dominio →
    ``save`` reemplaza el set completo. Cada query filtra por ``tenant_id``."""

    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def get(self, tenant_id: str, preparation_id: str) -> Preparation | None:
        async with self._session_factory() as session:
            row = (
                await session.execute(
                    select(PreparationORM).where(
                        PreparationORM.id == preparation_id,
                        PreparationORM.tenant_id == tenant_id,
                    )
                )
            ).scalar_one_or_none()
            if row is None:
                return None
            items = (
                await session.execute(
                    select(PreparationItemORM).where(
                        PreparationItemORM.preparation_id == preparation_id,
                        PreparationItemORM.tenant_id == tenant_id,
                    )
                )
            ).scalars().all()
            return preparation_to_domain(row, list(items))

    async def list(self, tenant_id: str) -> list[Preparation]:
        async with self._session_factory() as session:
            rows = (
                await session.execute(
                    select(PreparationORM)
                    .where(PreparationORM.tenant_id == tenant_id)
                    .order_by(PreparationORM.name)
                )
            ).scalars().all()
            if not rows:
                return []
            item_rows = (
                await session.execute(
                    select(PreparationItemORM).where(
                        PreparationItemORM.tenant_id == tenant_id
                    )
                )
            ).scalars().all()
            items_by_prep: dict[str, list[PreparationItemORM]] = {}
            for item in item_rows:
                items_by_prep.setdefault(item.preparation_id, []).append(item)
            return [
                preparation_to_domain(row, items_by_prep.get(row.id, []))
                for row in rows
            ]

    async def usage_counts(self, tenant_id: str) -> dict[str, int]:
        async with self._session_factory() as session:
            stmt = (
                select(
                    RecipeItemORM.preparation_id,
                    func.count(func.distinct(RecipeItemORM.product_id)),
                )
                .where(
                    RecipeItemORM.tenant_id == tenant_id,
                    RecipeItemORM.preparation_id.is_not(None),
                )
                .group_by(RecipeItemORM.preparation_id)
            )
            return {pid: int(n) for pid, n in (await session.execute(stmt)).all()}

    async def save(self, preparation: Preparation) -> None:
        async with self._session_factory() as session:
            await session.merge(preparation_to_orm(preparation))
            await session.execute(
                delete(PreparationItemORM).where(
                    PreparationItemORM.preparation_id == preparation.id,
                    PreparationItemORM.tenant_id == preparation.tenant_id,
                )
            )
            for item in preparation.items:
                session.add(preparation_item_to_orm(item, preparation, str(uuid4())))

    async def delete(self, tenant_id: str, preparation_id: str) -> None:
        async with self._session_factory() as session:
            await session.execute(
                delete(PreparationItemORM).where(
                    PreparationItemORM.preparation_id == preparation_id,
                    PreparationItemORM.tenant_id == tenant_id,
                )
            )
            await session.execute(
                delete(PreparationORM).where(
                    PreparationORM.id == preparation_id,
                    PreparationORM.tenant_id == tenant_id,
                )
            )
