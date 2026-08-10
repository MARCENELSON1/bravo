from __future__ import annotations

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, status

from app.application.inventory.food_cost import GetFoodCost
from app.application.inventory.preparations import (
    DeletePreparation,
    ListPreparations,
    SavePreparation,
)
from app.application.inventory.use_cases import (
    CreateIngredient,
    CreateSupplier,
    ListIngredients,
    ListLowStock,
    ListSuppliers,
    RegisterPurchase,
    RegisterWaste,
    UpdateIngredient,
)
from app.container import Container
from app.domain.identity.tokens import AccessClaims
from app.domain.inventory.entities import Ingredient, Supplier
from app.domain.inventory.recipe import Preparation, RecipeItem
from app.domain.user.value_objects import Role
from app.presentation.rbac import require_roles
from app.presentation.schemas.inventory import (
    CreateIngredientRequest,
    CreateIngredientResponse,
    CreatePreparationResponse,
    CreateSupplierRequest,
    CreateSupplierResponse,
    FoodCostResponse,
    FoodCostRowResponse,
    IngredientResponse,
    PreparationResponse,
    PurchaseRequest,
    RecipeItemSchema,
    SavePreparationRequest,
    SupplierResponse,
    UpdateIngredientRequest,
    WasteRequest,
)

router = APIRouter(prefix="/inventory", tags=["inventory"])


def _to_recipe_items(items: list[RecipeItemSchema]) -> list[RecipeItem]:
    return [
        RecipeItem(
            ingredient_id=i.ingredient_id, preparation_id=i.preparation_id, qty=i.qty
        )
        for i in items
    ]


def _preparation_response(
    prep: Preparation, used_in_products: int = 0
) -> PreparationResponse:
    return PreparationResponse(
        id=prep.id,
        name=prep.name,
        yield_qty=prep.yield_qty,
        used_in_products=used_in_products,
        items=[
            RecipeItemSchema(
                ingredient_id=item.ingredient_id,
                preparation_id=item.preparation_id,
                qty=item.qty,
            )
            for item in prep.items
        ],
    )


def _ingredient_response(ingredient: Ingredient) -> IngredientResponse:
    return IngredientResponse(
        id=ingredient.id,
        name=ingredient.name,
        unit=ingredient.unit.value,
        stock_qty=ingredient.stock_qty,
        min_qty=ingredient.min_qty,
        unit_cost_amount=ingredient.unit_cost.amount,
        currency=ingredient.unit_cost.currency,
        yield_pct=ingredient.yield_pct,
        cost_includes_tax=ingredient.cost_includes_tax,
        recipe_unit=ingredient.recipe_unit.value if ingredient.recipe_unit else None,
        active=ingredient.active,
        is_below_min=ingredient.is_below_min,
    )


def _supplier_response(supplier: Supplier) -> SupplierResponse:
    return SupplierResponse(
        id=supplier.id, name=supplier.name, contact=supplier.contact, active=supplier.active
    )


# --- Ingredients ----------------------------------------------------------


@router.post(
    "/ingredients",
    response_model=CreateIngredientResponse,
    status_code=status.HTTP_201_CREATED,
)
@inject
async def create_ingredient(
    body: CreateIngredientRequest,
    identity: AccessClaims = Depends(require_roles(Role.OWNER, Role.MANAGER)),
    use_case: CreateIngredient = Depends(Provide[Container.create_ingredient]),
) -> CreateIngredientResponse:
    ingredient = await use_case.execute(
        tenant_id=identity.tenant_id,
        name=body.name,
        unit=body.unit.value,
        min_qty=body.min_qty,
        unit_cost_amount=body.unit_cost_amount,
        stock_qty=body.stock_qty,
        yield_pct=body.yield_pct,
        price_includes_tax=body.price_includes_tax,
        recipe_unit=body.recipe_unit.value if body.recipe_unit else None,
    )
    return CreateIngredientResponse(ingredient_id=ingredient.id)


@router.get("/ingredients", response_model=list[IngredientResponse])
@inject
async def list_ingredients(
    active_only: bool = False,
    identity: AccessClaims = Depends(require_roles(Role.OWNER, Role.MANAGER)),
    use_case: ListIngredients = Depends(Provide[Container.list_ingredients]),
) -> list[IngredientResponse]:
    ingredients = await use_case.execute(
        tenant_id=identity.tenant_id, active_only=active_only
    )
    return [_ingredient_response(i) for i in ingredients]


@router.patch("/ingredients/{ingredient_id}", response_model=IngredientResponse)
@inject
async def update_ingredient(
    ingredient_id: str,
    body: UpdateIngredientRequest,
    identity: AccessClaims = Depends(require_roles(Role.OWNER, Role.MANAGER)),
    use_case: UpdateIngredient = Depends(Provide[Container.update_ingredient]),
) -> IngredientResponse:
    ingredient = await use_case.execute(
        tenant_id=identity.tenant_id,
        ingredient_id=ingredient_id,
        name=body.name,
        min_qty=body.min_qty,
        active=body.active,
        yield_pct=body.yield_pct,
        cost_includes_tax=body.cost_includes_tax,
    )
    return _ingredient_response(ingredient)


@router.post("/ingredients/{ingredient_id}/purchase", response_model=IngredientResponse)
@inject
async def register_purchase(
    ingredient_id: str,
    body: PurchaseRequest,
    identity: AccessClaims = Depends(require_roles(Role.OWNER, Role.MANAGER)),
    use_case: RegisterPurchase = Depends(Provide[Container.register_purchase]),
) -> IngredientResponse:
    ingredient = await use_case.execute(
        tenant_id=identity.tenant_id,
        ingredient_id=ingredient_id,
        qty=body.qty,
        unit_cost_amount=body.unit_cost_amount,
        price_includes_tax=body.price_includes_tax,
    )
    return _ingredient_response(ingredient)


@router.post("/ingredients/{ingredient_id}/waste", response_model=IngredientResponse)
@inject
async def register_waste(
    ingredient_id: str,
    body: WasteRequest,
    identity: AccessClaims = Depends(require_roles(Role.OWNER, Role.MANAGER)),
    use_case: RegisterWaste = Depends(Provide[Container.register_waste]),
) -> IngredientResponse:
    ingredient = await use_case.execute(
        tenant_id=identity.tenant_id,
        ingredient_id=ingredient_id,
        qty=body.qty,
        note=body.note,
    )
    return _ingredient_response(ingredient)


@router.get("/low-stock", response_model=list[IngredientResponse])
@inject
async def list_low_stock(
    identity: AccessClaims = Depends(require_roles(Role.OWNER, Role.MANAGER)),
    use_case: ListLowStock = Depends(Provide[Container.list_low_stock]),
) -> list[IngredientResponse]:
    ingredients = await use_case.execute(tenant_id=identity.tenant_id)
    return [_ingredient_response(i) for i in ingredients]


@router.get("/food-cost", response_model=FoodCostResponse)
@inject
async def get_food_cost(
    identity: AccessClaims = Depends(require_roles(Role.OWNER, Role.MANAGER)),
    use_case: GetFoodCost = Depends(Provide[Container.get_food_cost]),
) -> FoodCostResponse:
    report = await use_case.execute(tenant_id=identity.tenant_id)
    return FoodCostResponse(
        currency=report.currency,
        rows=[
            FoodCostRowResponse(
                product_id=r.product_id,
                product_name=r.product_name,
                price_amount=r.price_amount,
                food_cost_amount=r.food_cost_amount,
                margin_amount=r.margin_amount,
                food_cost_ratio_bps=r.food_cost_ratio_bps,
                currency=r.currency,
            )
            for r in report.rows
        ],
    )


# --- Preparaciones (recetas madre) ------------------------------------------


@router.get("/preparations", response_model=list[PreparationResponse])
@inject
async def list_preparations(
    identity: AccessClaims = Depends(require_roles(Role.OWNER, Role.MANAGER)),
    use_case: ListPreparations = Depends(Provide[Container.list_preparations]),
) -> list[PreparationResponse]:
    preparations = await use_case.execute(tenant_id=identity.tenant_id)
    return [
        _preparation_response(p.preparation, p.used_in_products) for p in preparations
    ]


@router.post(
    "/preparations",
    response_model=CreatePreparationResponse,
    status_code=status.HTTP_201_CREATED,
)
@inject
async def create_preparation(
    body: SavePreparationRequest,
    identity: AccessClaims = Depends(require_roles(Role.OWNER, Role.MANAGER)),
    use_case: SavePreparation = Depends(Provide[Container.save_preparation]),
) -> CreatePreparationResponse:
    prep = await use_case.execute(
        tenant_id=identity.tenant_id,
        preparation_id=None,
        name=body.name,
        yield_qty=body.yield_qty,
        items=_to_recipe_items(body.items),
    )
    return CreatePreparationResponse(preparation_id=prep.id)


@router.put("/preparations/{preparation_id}", response_model=PreparationResponse)
@inject
async def update_preparation(
    preparation_id: str,
    body: SavePreparationRequest,
    identity: AccessClaims = Depends(require_roles(Role.OWNER, Role.MANAGER)),
    use_case: SavePreparation = Depends(Provide[Container.save_preparation]),
) -> PreparationResponse:
    prep = await use_case.execute(
        tenant_id=identity.tenant_id,
        preparation_id=preparation_id,
        name=body.name,
        yield_qty=body.yield_qty,
        items=_to_recipe_items(body.items),
    )
    return _preparation_response(prep)


@router.delete(
    "/preparations/{preparation_id}", status_code=status.HTTP_204_NO_CONTENT
)
@inject
async def delete_preparation(
    preparation_id: str,
    identity: AccessClaims = Depends(require_roles(Role.OWNER, Role.MANAGER)),
    use_case: DeletePreparation = Depends(Provide[Container.delete_preparation]),
) -> None:
    await use_case.execute(tenant_id=identity.tenant_id, preparation_id=preparation_id)


# --- Suppliers ------------------------------------------------------------


@router.post(
    "/suppliers",
    response_model=CreateSupplierResponse,
    status_code=status.HTTP_201_CREATED,
)
@inject
async def create_supplier(
    body: CreateSupplierRequest,
    identity: AccessClaims = Depends(require_roles(Role.OWNER, Role.MANAGER)),
    use_case: CreateSupplier = Depends(Provide[Container.create_supplier]),
) -> CreateSupplierResponse:
    supplier = await use_case.execute(
        tenant_id=identity.tenant_id, name=body.name, contact=body.contact
    )
    return CreateSupplierResponse(supplier_id=supplier.id)


@router.get("/suppliers", response_model=list[SupplierResponse])
@inject
async def list_suppliers(
    active_only: bool = False,
    identity: AccessClaims = Depends(require_roles(Role.OWNER, Role.MANAGER)),
    use_case: ListSuppliers = Depends(Provide[Container.list_suppliers]),
) -> list[SupplierResponse]:
    suppliers = await use_case.execute(
        tenant_id=identity.tenant_id, active_only=active_only
    )
    return [_supplier_response(s) for s in suppliers]
