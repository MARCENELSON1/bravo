from __future__ import annotations

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, status

from app.application.table.use_cases import CreateTable, ListTables
from app.container import Container
from app.domain.identity.tokens import AccessClaims
from app.domain.user.value_objects import Role
from app.presentation.deps import current_identity
from app.presentation.rbac import require_roles
from app.presentation.schemas.tables import (
    CreateTableRequest,
    CreateTableResponse,
    TableResponse,
)

router = APIRouter(prefix="/tables", tags=["tables"])


@router.post("", response_model=CreateTableResponse, status_code=status.HTTP_201_CREATED)
@inject
async def create_table(
    body: CreateTableRequest,
    identity: AccessClaims = Depends(require_roles(Role.OWNER, Role.MANAGER)),
    use_case: CreateTable = Depends(Provide[Container.create_table]),
) -> CreateTableResponse:
    result = await use_case.execute(
        tenant_id=identity.tenant_id, number=body.number, name=body.name
    )
    return CreateTableResponse(table_id=result.table_id)


@router.get("", response_model=list[TableResponse])
@inject
async def list_tables(
    identity: AccessClaims = Depends(current_identity),
    use_case: ListTables = Depends(Provide[Container.list_tables]),
) -> list[TableResponse]:
    tables = await use_case.execute(tenant_id=identity.tenant_id)
    return [
        TableResponse(id=t.id, number=t.number, name=t.name, active=t.active)
        for t in tables
    ]
