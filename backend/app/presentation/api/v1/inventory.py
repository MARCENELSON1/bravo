from __future__ import annotations

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, status

from app.application.inventory.food_cost import GetFoodCost
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
from app.domain.user.value_objects import Role
from app.presentation.rbac import require_roles
from app.presentation.schemas.inventory import (
    CreateIngredientRequest,
    CreateIngredientResponse,
    CreateSupplierRequest,
    CreateSupplierResponse,
    FoodCostResponse,
    FoodCostRowResponse,
    IngredientResponse,
    PurchaseRequest,
    SupplierResponse,
    UpdateIngredientRequest,
    WasteRequest,
)

router = APIRouter(prefix="/inventory", tags=["inventory"])


def _ingredient_response(ingredient: Ingredient) -> IngredientResponse:
    return IngredientResponse(
        id=ingredient.id,
        name=ingredient.name,
        unit=ingredient.unit.value,
        stock_qty=ingredient.stock_qty,
        min_qty=ingredient.min_qty,
        unit_cost_amount=ingredient.unit_cost.amount,
        currency=ingredient.unit_cost.currency,
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
