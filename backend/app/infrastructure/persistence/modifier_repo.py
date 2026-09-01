from __future__ import annotations

from sqlalchemy import delete, select

from app.domain.product.modifier_repository import ModifierRepository
from app.domain.product.modifiers import ModifierGroup
from app.infrastructure.persistence.database import SessionFactory
from app.infrastructure.persistence.mappers import (
    modifier_group_to_domain,
    modifier_group_to_orm,
    modifier_option_to_orm,
)
from app.infrastructure.persistence.models import (
    ProductModifierGroupORM,
    ProductModifierOptionORM,
)


class SqlAlchemyModifierRepository(ModifierRepository):
    """Modifier groups + options for a product. Groups have no independent
    lifecycle, so ``replace_for_product`` swaps the whole set (mirrors the recipe
    repo). Every query is scoped by ``tenant_id`` (RLS as the safety net)."""

    def __init__(self, session_factory: SessionFactory) -> None:
        self._session_factory = session_factory

    async def list_for_product(
        self, tenant_id: str, product_id: str
    ) -> list[ModifierGroup]:
        return (await self.list_for_products(tenant_id, [product_id])).get(product_id, [])

    async def list_for_products(
        self, tenant_id: str, product_ids: list[str]
    ) -> dict[str, list[ModifierGroup]]:
        if not product_ids:
            return {}
        async with self._session_factory() as session:
            group_rows = (
                await session.execute(
                    select(ProductModifierGroupORM).where(
                        ProductModifierGroupORM.tenant_id == tenant_id,
                        ProductModifierGroupORM.product_id.in_(product_ids),
                    )
                )
            ).scalars().all()
            if not group_rows:
                return {}
            group_ids = [g.id for g in group_rows]
            option_rows = (
                await session.execute(
                    select(ProductModifierOptionORM).where(
                        ProductModifierOptionORM.tenant_id == tenant_id,
                        ProductModifierOptionORM.group_id.in_(group_ids),
                    )
                )
            ).scalars().all()
            options_by_group: dict[str, list[ProductModifierOptionORM]] = {}
            for option in option_rows:
                options_by_group.setdefault(option.group_id, []).append(option)
            result: dict[str, list[ModifierGroup]] = {}
            for group in sorted(group_rows, key=lambda g: g.position):
                result.setdefault(group.product_id, []).append(
                    modifier_group_to_domain(group, options_by_group.get(group.id, []))
                )
            return result

    async def replace_for_product(
        self, tenant_id: str, product_id: str, groups: list[ModifierGroup]
    ) -> None:
        async with self._session_factory() as session:
            # Options cascade off their group (FK ondelete=CASCADE), so deleting the
            # product's groups clears its options too.
            await session.execute(
                delete(ProductModifierGroupORM).where(
                    ProductModifierGroupORM.tenant_id == tenant_id,
                    ProductModifierGroupORM.product_id == product_id,
                )
            )
            await session.flush()  # apply the delete before re-inserting the new set
            for gpos, group in enumerate(groups):
                session.add(modifier_group_to_orm(group, gpos))
                for opos, option in enumerate(group.options):
                    session.add(modifier_option_to_orm(option, group, opos))
