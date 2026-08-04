"""Preparaciones (recetas madre) — CRUD con guard anti-ciclo al guardar.

Una preparación referencia insumos y/o sub-preparaciones. Al guardar se valida
que los componentes existan y que el grafo de preparaciones no forme un ciclo
(reusa ``resolve_preparation_costs``, que levanta ``RecipeCycle``)."""

from __future__ import annotations

from uuid import uuid4

from app.domain.identity.ports import TenantContext
from app.domain.inventory.costing import resolve_preparation_costs
from app.domain.inventory.exceptions import (
    IngredientNotFound,
    PreparationNotFound,
    RecipeCycle,
)
from app.domain.inventory.recipe import Preparation, RecipeItem
from app.domain.inventory.repository import (
    IngredientRepository,
    PreparationRepository,
)

# El guard de ciclos es agnóstico de la moneda (solo recorre el grafo).
_GUARD_CURRENCY = "ARS"


class ListPreparations:
    def __init__(
        self, preparations: PreparationRepository, tenant_context: TenantContext
    ) -> None:
        self._preparations = preparations
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str) -> list[Preparation]:
        self._tenant_context.set(tenant_id)
        return await self._preparations.list(tenant_id)


class SavePreparation:
    """Crea o actualiza una preparación (receta madre). Valida existencia de los
    componentes y rechaza ciclos (directos o indirectos)."""

    def __init__(
        self,
        preparations: PreparationRepository,
        ingredients: IngredientRepository,
        tenant_context: TenantContext,
    ) -> None:
        self._preparations = preparations
        self._ingredients = ingredients
        self._tenant_context = tenant_context

    async def execute(
        self,
        *,
        tenant_id: str,
        preparation_id: str | None,
        name: str,
        yield_qty: int,
        items: list[RecipeItem],
    ) -> Preparation:
        self._tenant_context.set(tenant_id)
        prep_id = preparation_id or str(uuid4())
        existing = await self._preparations.list(tenant_id)
        known_ingredients = {i.id for i in await self._ingredients.list(tenant_id)}
        known_preparations = {p.id for p in existing}

        for item in items:
            if item.ingredient_id is not None and item.ingredient_id not in known_ingredients:
                raise IngredientNotFound()
            if item.preparation_id is not None:
                if item.preparation_id == prep_id:
                    raise RecipeCycle()  # auto-referencia directa
                if item.preparation_id not in known_preparations:
                    raise PreparationNotFound()

        preparation = Preparation(
            id=prep_id,
            tenant_id=tenant_id,
            name=name,
            yield_qty=yield_qty,
            items=items,
        )
        # Guard anti-ciclo: resolver el grafo con esta preparación reemplazada.
        graph = {p.id: p for p in existing}
        graph[prep_id] = preparation
        resolve_preparation_costs(graph, {}, _GUARD_CURRENCY)  # levanta RecipeCycle
        await self._preparations.save(preparation)
        return preparation


class DeletePreparation:
    """Borra una preparación. Los ítems de receta que la referencian quedan con
    costo desconocido (0) hasta que se corrijan — no se bloquea el borrado."""

    def __init__(
        self, preparations: PreparationRepository, tenant_context: TenantContext
    ) -> None:
        self._preparations = preparations
        self._tenant_context = tenant_context

    async def execute(self, *, tenant_id: str, preparation_id: str) -> None:
        self._tenant_context.set(tenant_id)
        existing = await self._preparations.get(tenant_id, preparation_id)
        if existing is None:
            raise PreparationNotFound()
        await self._preparations.delete(tenant_id, preparation_id)
