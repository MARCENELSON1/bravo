from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.inventory.entities import Ingredient, StockMovement, Supplier
from app.domain.inventory.recipe import Recipe


class IngredientRepository(ABC):
    """Port for ingredient persistence. Every method is scoped by ``tenant_id``."""

    @abstractmethod
    async def get_by_id(self, tenant_id: str, ingredient_id: str) -> Ingredient | None: ...

    @abstractmethod
    async def list_below_min(self, tenant_id: str) -> list[Ingredient]: ...

    @abstractmethod
    async def list(self, tenant_id: str, *, active_only: bool = False) -> list[Ingredient]: ...

    @abstractmethod
    async def add(self, ingredient: Ingredient) -> None: ...

    @abstractmethod
    async def save(self, ingredient: Ingredient) -> None: ...


class SupplierRepository(ABC):
    """Port for supplier persistence. Every method is scoped by ``tenant_id``."""

    @abstractmethod
    async def get_by_id(self, tenant_id: str, supplier_id: str) -> Supplier | None: ...

    @abstractmethod
    async def list(self, tenant_id: str, *, active_only: bool = False) -> list[Supplier]: ...

    @abstractmethod
    async def add(self, supplier: Supplier) -> None: ...

    @abstractmethod
    async def save(self, supplier: Supplier) -> None: ...


class RecipeRepository(ABC):
    """Port for recipe persistence (1:1 with a product). Scoped by ``tenant_id``."""

    @abstractmethod
    async def get_for_product(self, tenant_id: str, product_id: str) -> Recipe | None: ...

    @abstractmethod
    async def list_for_products(
        self, tenant_id: str, product_ids: list[str]
    ) -> dict[str, Recipe]: ...

    @abstractmethod
    async def save(self, recipe: Recipe) -> None: ...


class StockMovementRepository(ABC):
    """Port for stock-movement persistence. Every method is scoped by ``tenant_id``."""

    @abstractmethod
    async def add(self, movement: StockMovement) -> None: ...

    @abstractmethod
    async def exists_for_order(self, tenant_id: str, order_id: str) -> bool: ...

    @abstractmethod
    async def list_for_ingredient(
        self, tenant_id: str, ingredient_id: str
    ) -> list[StockMovement]: ...
