from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.product.entities import Product


class ProductRepository(ABC):
    """Port for product persistence. Every method is scoped by ``tenant_id``."""

    @abstractmethod
    async def get_by_id(self, tenant_id: str, product_id: str) -> Product | None: ...

    @abstractmethod
    async def list(self, tenant_id: str, *, only_active: bool = False) -> list[Product]: ...

    @abstractmethod
    async def add(self, product: Product) -> None: ...

    @abstractmethod
    async def save(self, product: Product) -> None: ...
