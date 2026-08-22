from __future__ import annotations

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, status

from app.application.table.use_cases import CreateTable, ListTables, UpdateTable
from app.container import Container
from app.domain.identity.tokens import AccessClaims
from app.domain.user.value_objects import Role
from app.presentation.deps import current_identity
from app.presentation.rbac import require_roles
from app.presentation.schemas.tables import (
    CreateTableRequest,
    CreateTableResponse,
    TableResponse,
    UpdateTableRequest,
)

router = APIRouter(prefix="/tables", tags=["tables"])


def _table_response(t) -> TableResponse:
    return TableResponse(
        id=t.id,
        number=t.number,
        name=t.name,
        active=t.active,
        sector_id=t.sector_id,
        capacity=t.capacity,
    )


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
    return [_table_response(t) for t in tables]


@router.patch("/{table_id}", response_model=TableResponse)
@inject
async def update_table(
    table_id: str,
    body: UpdateTableRequest,
    identity: AccessClaims = Depends(require_roles(Role.OWNER, Role.MANAGER)),
    use_case: UpdateTable = Depends(Provide[Container.update_table]),
) -> TableResponse:
    # Only touch the fields the client actually sent (PATCH semantics): omitted
    # fields aren't passed at all, so the use case leaves them untouched.
    sent = body.model_fields_set
    patch: dict[str, object] = {}
    if "sector_id" in sent:
        patch["sector_id"] = body.sector_id
    if "capacity" in sent:
        patch["capacity"] = body.capacity
    table = await use_case.execute(
        tenant_id=identity.tenant_id, table_id=table_id, **patch
    )
    return _table_response(table)
