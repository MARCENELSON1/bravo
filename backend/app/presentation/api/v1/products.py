from __future__ import annotations

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, status

from app.application.product.use_cases import CreateProduct, ListProducts
from app.container import Container
from app.domain.identity.tokens import AccessClaims
from app.domain.user.value_objects import Role
from app.presentation.deps import current_identity
from app.presentation.rbac import require_roles
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
            active=p.active,
        )
        for p in products
    ]
