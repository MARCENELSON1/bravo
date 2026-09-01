from __future__ import annotations

from datetime import datetime

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query, status

from app.application.inventory.use_cases import GetRecipe, SetRecipe
from app.application.product.modifiers import (
    GetProductModifiers,
    ModifierGroupSpec,
    ModifierOptionSpec,
    SetProductModifiers,
)
from app.application.product.use_cases import (
    CreateProduct,
    GetPricingInsights,
    GetProductPriceHistory,
    GetProductRotation,
    ListProducts,
    SetProductAvailability,
    UpdateProductPrice,
)
from app.container import Container
from app.domain.identity.tokens import AccessClaims
from app.domain.inventory.recipe import RecipeItem
from app.domain.product.entities import Product
from app.domain.product.modifiers import ModifierGroup
from app.domain.user.value_objects import Role
from app.presentation.deps import current_identity
from app.presentation.rbac import require_roles
from app.presentation.schemas.inventory import (
    RecipeItemSchema,
    RecipeResponse,
    SetRecipeRequest,
)
from app.presentation.schemas.modifiers import (
    ModifierGroupResponse,
    ModifierOptionResponse,
    ProductModifiersResponse,
    SetModifiersRequest,
)
from app.presentation.schemas.products import (
    CreateProductRequest,
    CreateProductResponse,
    PriceChangeResponse,
    PricingInsightsResponse,
    PricingRowResponse,
    ProductPriceHistoryResponse,
    ProductResponse,
    ProductRotationResponse,
    SetAvailabilityRequest,
    UpdateProductPriceRequest,
    WeekdayRotationResponse,
)

router = APIRouter(prefix="/products", tags=["products"])


def _product_response(p: Product) -> ProductResponse:
    return ProductResponse(
        id=p.id,
        name=p.name,
        price_amount=p.price.amount,
        currency=p.price.currency,
        category=p.category,
        station=p.station.value,
        active=p.active,
        image_url=p.image_url,
        description=p.description,
        available_today=p.available_today,
    )


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
        image_url=body.image_url,
        description=body.description,
    )
    return CreateProductResponse(product_id=result.product_id)


@router.get("", response_model=list[ProductResponse])
@inject
async def list_products(
    identity: AccessClaims = Depends(current_identity),
    use_case: ListProducts = Depends(Provide[Container.list_products]),
) -> list[ProductResponse]:
    products = await use_case.execute(tenant_id=identity.tenant_id)
    return [_product_response(p) for p in products]


@router.put("/{product_id}/availability", response_model=ProductResponse)
@inject
async def set_product_availability(
    product_id: str,
    body: SetAvailabilityRequest,
    identity: AccessClaims = Depends(require_roles(Role.OWNER, Role.MANAGER)),
    use_case: SetProductAvailability = Depends(Provide[Container.set_product_availability]),
) -> ProductResponse:
    # "86'd" toggle: agotado hoy (no toca `active`).
    product = await use_case.execute(
        tenant_id=identity.tenant_id,
        product_id=product_id,
        available_today=body.available_today,
    )
    return _product_response(product)


# --- Productos v2 Tanda B: precios vs inflación + histórico + rotación --------


@router.get("/pricing", response_model=PricingInsightsResponse)
@inject
async def get_pricing_insights(
    identity: AccessClaims = Depends(require_roles(Role.OWNER, Role.MANAGER)),
    use_case: GetPricingInsights = Depends(Provide[Container.get_pricing_insights]),
) -> PricingInsightsResponse:
    insights = await use_case.execute(tenant_id=identity.tenant_id)
    return PricingInsightsResponse(
        currency=insights.currency,
        monthly_inflation_bps=insights.monthly_inflation_bps,
        configured=insights.configured,
        rows=[
            PricingRowResponse(
                product_id=r.product_id,
                product_name=r.product_name,
                current_price_amount=r.current_price_amount,
                suggested_price_amount=r.suggested_price_amount,
                gap_amount=r.gap_amount,
                gap_bps=r.gap_bps,
                days_since_change=r.days_since_change,
                lagging=r.lagging,
            )
            for r in insights.rows
        ],
    )


@router.get("/rotation", response_model=ProductRotationResponse)
@inject
async def get_product_rotation(
    since: datetime | None = Query(default=None, alias="from"),
    until: datetime | None = Query(default=None, alias="to"),
    identity: AccessClaims = Depends(require_roles(Role.OWNER, Role.MANAGER)),
    use_case: GetProductRotation = Depends(Provide[Container.get_product_rotation]),
) -> ProductRotationResponse:
    rotation = await use_case.execute(
        tenant_id=identity.tenant_id, since=since, until=until
    )
    return ProductRotationResponse(
        currency=rotation.currency,
        rows=[
            WeekdayRotationResponse(
                weekday=r.weekday,
                units=r.units,
                sales_amount=r.sales_amount,
                top_product_name=r.top_product_name,
            )
            for r in rotation.rows
        ],
    )


@router.put("/{product_id}/price", response_model=ProductResponse)
@inject
async def update_product_price(
    product_id: str,
    body: UpdateProductPriceRequest,
    identity: AccessClaims = Depends(require_roles(Role.OWNER, Role.MANAGER)),
    use_case: UpdateProductPrice = Depends(Provide[Container.update_product_price]),
) -> ProductResponse:
    product = await use_case.execute(
        tenant_id=identity.tenant_id,
        product_id=product_id,
        new_price_amount=body.price_amount,
    )
    return _product_response(product)


@router.get("/{product_id}/price-history", response_model=ProductPriceHistoryResponse)
@inject
async def get_product_price_history(
    product_id: str,
    identity: AccessClaims = Depends(require_roles(Role.OWNER, Role.MANAGER)),
    use_case: GetProductPriceHistory = Depends(
        Provide[Container.get_product_price_history]
    ),
) -> ProductPriceHistoryResponse:
    history = await use_case.execute(tenant_id=identity.tenant_id, product_id=product_id)
    return ProductPriceHistoryResponse(
        product_id=history.product_id,
        currency=history.currency,
        changes=[
            PriceChangeResponse(
                changed_at=c.changed_at,
                old_price_amount=c.old_price_amount,
                new_price_amount=c.new_price_amount,
            )
            for c in history.changes
        ],
    )


# --- Modifiers (opt-in, Carta QR F2 D): choices the diner picks per item -----


def _modifiers_response(product_id: str, groups: list[ModifierGroup]) -> ProductModifiersResponse:
    return ProductModifiersResponse(
        product_id=product_id,
        groups=[
            ModifierGroupResponse(
                id=g.id,
                name=g.name,
                min_select=g.min_select,
                max_select=g.max_select,
                required=g.required,
                options=[
                    ModifierOptionResponse(id=o.id, name=o.name, price_delta=o.price_delta)
                    for o in g.options
                ],
            )
            for g in groups
        ],
    )


@router.get("/{product_id}/modifiers", response_model=ProductModifiersResponse)
@inject
async def get_product_modifiers(
    product_id: str,
    identity: AccessClaims = Depends(require_roles(Role.OWNER, Role.MANAGER)),
    use_case: GetProductModifiers = Depends(Provide[Container.get_product_modifiers]),
) -> ProductModifiersResponse:
    groups = await use_case.execute(tenant_id=identity.tenant_id, product_id=product_id)
    return _modifiers_response(product_id, groups)


@router.put("/{product_id}/modifiers", response_model=ProductModifiersResponse)
@inject
async def set_product_modifiers(
    product_id: str,
    body: SetModifiersRequest,
    identity: AccessClaims = Depends(require_roles(Role.OWNER, Role.MANAGER)),
    use_case: SetProductModifiers = Depends(Provide[Container.set_product_modifiers]),
) -> ProductModifiersResponse:
    groups = await use_case.execute(
        tenant_id=identity.tenant_id,
        product_id=product_id,
        groups=[
            ModifierGroupSpec(
                name=g.name,
                min_select=g.min_select,
                max_select=g.max_select,
                options=[
                    ModifierOptionSpec(name=o.name, price_delta=o.price_delta)
                    for o in g.options
                ],
            )
            for g in body.groups
        ],
    )
    return _modifiers_response(product_id, groups)


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
        version=recipe.version,
        items=[
            RecipeItemSchema(
                ingredient_id=item.ingredient_id,
                preparation_id=item.preparation_id,
                qty=item.qty,
            )
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
        items=[
            RecipeItem(
                ingredient_id=item.ingredient_id,
                preparation_id=item.preparation_id,
                qty=item.qty,
            )
            for item in body.items
        ],
    )
    return RecipeResponse(
        product_id=product_id,
        has_recipe=True,
        version=recipe.version,
        items=[
            RecipeItemSchema(
                ingredient_id=item.ingredient_id,
                preparation_id=item.preparation_id,
                qty=item.qty,
            )
            for item in recipe.items
        ],
    )
