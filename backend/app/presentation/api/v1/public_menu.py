"""Carta pública (QR de mesa) — endpoint SIN auth. El comensal escanea el QR de su
mesa y ve la carta del local: el token porta el tenant, así que no hace falta login.
Solo lectura y solo lo público (activos, sin costos). Molde: ``public.py``/``leads.py``."""

from __future__ import annotations

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query

from app.application.public_menu.use_cases import GetPublicMenu
from app.container import Container
from app.presentation.schemas.public_menu import (
    PublicMenuCategoryResponse,
    PublicMenuItemResponse,
    PublicMenuResponse,
)

router = APIRouter(prefix="/public", tags=["public-menu"])


@router.get("/menu", response_model=PublicMenuResponse)
@inject
async def get_public_menu(
    token: str = Query(...),
    use_case: GetPublicMenu = Depends(Provide[Container.get_public_menu]),
) -> PublicMenuResponse:
    menu = await use_case.execute(token=token)
    return PublicMenuResponse(
        tenant_name=menu.tenant_name,
        currency=menu.currency,
        locale=menu.locale,
        categories=[
            PublicMenuCategoryResponse(
                name=category.name,
                items=[
                    PublicMenuItemResponse(
                        id=item.id, name=item.name, price_amount=item.price_amount
                    )
                    for item in category.items
                ],
            )
            for category in menu.categories
        ],
    )
