from __future__ import annotations

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends

from app.application.copilot.ask import AskCopilot
from app.container import Container
from app.domain.identity.tokens import AccessClaims
from app.domain.user.value_objects import Role
from app.presentation.rbac import require_roles
from app.presentation.schemas.copilot import AskCopilotRequest, CopilotAnswerResponse

router = APIRouter(prefix="/copilot", tags=["copilot"])


@router.post("/ask", response_model=CopilotAnswerResponse)
@inject
async def ask(
    body: AskCopilotRequest,
    identity: AccessClaims = Depends(require_roles(Role.OWNER, Role.MANAGER)),
    use_case: AskCopilot = Depends(Provide[Container.ask_copilot]),
) -> CopilotAnswerResponse:
    result = await use_case.execute(tenant_id=identity.tenant_id, question=body.question)
    return CopilotAnswerResponse(
        answer=result.answer,
        sql=result.sql,
        columns=result.columns,
        rows=result.rows,
        llm_enabled=result.llm_enabled,
    )
