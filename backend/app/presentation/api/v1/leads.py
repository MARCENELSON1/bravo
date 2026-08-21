"""Captación de la landing. Endpoint PÚBLICO (sin auth): lo llama wellnod.com,
que es un sitio estático y por eso no puede sostener credenciales del CRM."""

from __future__ import annotations

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, status

from app.application.marketing.submit_lead import SubmitLead
from app.container import Container
from app.presentation.schemas.leads import LeadRequest, LeadResponse

router = APIRouter(prefix="/leads", tags=["leads"])


@router.post("", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
@inject
async def submit_lead(
    body: LeadRequest,
    use_case: SubmitLead = Depends(Provide[Container.submit_lead]),
) -> LeadResponse:
    await use_case.execute(email=body.email, name=body.name, message=body.message)
    return LeadResponse(message="¡Listo! Recibimos tus datos.")
