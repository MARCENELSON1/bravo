from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from app.domain.identity.ports import TenantContext
from app.domain.product.exceptions import ProductNotFound
from app.domain.product.modifier_repository import ModifierRepository
from app.domain.product.modifiers import ModifierGroup, ModifierOption
from app.domain.product.repository import ProductRepository


@dataclass(frozen=True)
class ModifierOptionSpec:
    name: str
    price_delta: int = 0


@dataclass(frozen=True)
class ModifierGroupSpec:
    """What the owner sends to define a group (no ids — they're minted on save)."""

    name: str
    min_select: int
    max_select: int
    options: list[ModifierOptionSpec] = field(default_factory=list)


class GetProductModifiers:
    def __init__(
        self, modifiers: ModifierRepository, tenant_context: TenantContext
    ) -> None:
        self._modifiers = modifiers
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str, product_id: str) -> list[ModifierGroup]:
        self._tenant_context.set(tenant_id)
        return await self._modifiers.list_for_product(tenant_id, product_id)


class SetProductModifiers:
    """Owner/manager action: replace a product's modifier groups. Ids are minted
    server-side on every save (replace-all, mirrors ``SetRecipe``) — a live order
    already snapshotted the options it used, so regenerating ids is safe."""

    def __init__(
        self,
        modifiers: ModifierRepository,
        products: ProductRepository,
        tenant_context: TenantContext,
    ) -> None:
        self._modifiers = modifiers
        self._products = products
        self._tenant_context = tenant_context

    async def execute(
        self, *, tenant_id: str, product_id: str, groups: list[ModifierGroupSpec]
    ) -> list[ModifierGroup]:
        self._tenant_context.set(tenant_id)
        product = await self._products.get_by_id(tenant_id, product_id)
        if product is None:
            raise ProductNotFound()
        built = [
            ModifierGroup(
                id=str(uuid4()),
                tenant_id=tenant_id,
                product_id=product_id,
                name=spec.name,
                min_select=spec.min_select,
                max_select=spec.max_select,
                options=[
                    ModifierOption(id=str(uuid4()), name=o.name, price_delta=o.price_delta)
                    for o in spec.options
                ],
            )
            for spec in groups
        ]  # ModifierGroup.__post_init__ validates min/max/options → InvalidModifierGroup
        await self._modifiers.replace_for_product(tenant_id, product_id, built)
        return built
