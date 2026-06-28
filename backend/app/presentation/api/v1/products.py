from __future__ import annotations

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, status

from app.application.inventory.use_cases import GetRecipe, SetRecipe
from app.application.product.use_cases import CreateProduct, ListProducts
from app.container import Container
from app.domain.identity.tokens import AccessClaims
from app.domain.user.value_objects import Role
from app.presentation.deps import current_identity
from app.presentation.rbac import require_roles
from app.presentation.schemas.inventory import (
    RecipeItemSchema,
    RecipeResponse,
    SetRecipeRequest,
)
from app.presentation.schemas.products import (
    CreateProductRequest,
    CreateProductResponse,
    ProductResponse,
)

router = APIRouter(prefix="/products", tags=["products"])


@router.post("", response_model=CreateProductResponse, status_code=status.HTTP_201_CREATED)
@inject
async def create_product(
    body: CreateProductRequest,
    identity: AccessClaims = Depends(require_roles(Role.OWNER, Role.MANAGER)),
    use_case: CreateProduct = Depends(Provide[Container.create_product]),
) -> CreateProductResponse:
    result = await use_case.execute(
        tenant_id=identity.tenant_id,
        name=body.name,
        price_amount=body.price_amount,
        category=body.category,
        station=body.station,
    )
    return CreateProductResponse(product_id=result.product_id)


@router.get("", response_model=list[ProductResponse])
@inject
async def list_products(
    identity: AccessClaims = Depends(current_identity),
    use_case: ListProducts = Depends(Provide[Container.list_products]),
) -> list[ProductResponse]:
    products = await use_case.execute(tenant_id=identity.tenant_id)
    return [
        ProductResponse(
            id=p.id,
            name=p.name,
            price_amount=p.price.amount,
            currency=p.price.currency,
            category=p.category,
            station=p.station.value,
            active=p.active,
        )
        for p in products
    ]


# --- Recipe (opt-in, Fase 6): a product may or may not have one ----------


@router.get("/{product_id}/recipe", response_model=RecipeResponse)
@inject
async def get_product_recipe(
    product_id: str,
    identity: AccessClaims = Depends(require_roles(Role.OWNER, Role.MANAGER)),
    use_case: GetRecipe = Depends(Provide[Container.get_recipe]),
) -> RecipeResponse:
    recipe = await use_case.execute(tenant_id=identity.tenant_id, product_id=product_id)
    if recipe is None:
        return RecipeResponse(product_id=product_id, has_recipe=False, items=[])
    return RecipeResponse(
        product_id=product_id,
        has_recipe=True,
        items=[
            RecipeItemSchema(ingredient_id=item.ingredient_id, qty=item.qty)
            for item in recipe.items
        ],
    )


@router.put("/{product_id}/recipe", response_model=RecipeResponse)
@inject
async def set_product_recipe(
    product_id: str,
    body: SetRecipeRequest,
    identity: AccessClaims = Depends(require_roles(Role.OWNER, Role.MANAGER)),
    use_case: SetRecipe = Depends(Provide[Container.set_recipe]),
) -> RecipeResponse:
    recipe = await use_case.execute(
        tenant_id=identity.tenant_id,
        product_id=product_id,
        items=[(item.ingredient_id, item.qty) for item in body.items],
    )
    return RecipeResponse(
        product_id=product_id,
        has_recipe=True,
        items=[
            RecipeItemSchema(ingredient_id=item.ingredient_id, qty=item.qty)
            for item in recipe.items
        ],
    )
