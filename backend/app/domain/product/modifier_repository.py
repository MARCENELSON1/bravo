from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.product.modifiers import ModifierGroup


class ModifierRepository(ABC):
    """Port for a product's modifier groups + options. Scoped by ``tenant_id``.
    Groups have no independent lifecycle — ``replace_for_product`` swaps the whole
    set for a product (mirrors the recipe repository)."""

    @abstractmethod
    async def list_for_product(
        self, tenant_id: str, product_id: str
    ) -> list[ModifierGroup]: ...

    @abstractmethod
    async def list_for_products(
        self, tenant_id: str, product_ids: list[str]
    ) -> dict[str, list[ModifierGroup]]: ...

    @abstractmethod
    async def replace_for_product(
        self, tenant_id: str, product_id: str, groups: list[ModifierGroup]
    ) -> None: ...
