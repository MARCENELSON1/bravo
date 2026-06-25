from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.config import Settings
from app.container import Container
from app.domain.identity.ports import TokenService
from app.domain.identity.tokens import AccessClaims
from app.domain.realtime.ports import EventBus
from app.domain.user.value_objects import Role
from app.presentation.rbac import require_roles

router = APIRouter(prefix="/realtime", tags=["realtime"])

_STREAM_ROLES = (Role.KITCHEN, Role.MANAGER, Role.OWNER)


@router.post("/token")
@inject
async def issue_stream_token(
    identity: AccessClaims = Depends(require_roles(*_STREAM_ROLES)),
    tokens: TokenService = Depends(Provide[Container.token_service]),
    config: Settings = Depends(Provide[Container.config]),
) -> dict[str, object]:
    """Issue a short-lived, tenant-scoped token to open an SSE stream.

    RBAC is enforced here (Bearer-authenticated); the stream then only needs the
    token. EventSource can't send an Authorization header, hence this dance.
    """
    token = tokens.create_stream_token(
        tenant_id=identity.tenant_id, ttl_seconds=config.realtime_token_ttl_s
    )
    return {"token": token, "expires_in": config.realtime_token_ttl_s}


def _sse_response(bus: EventBus, tenant_id: str, heartbeat: int) -> StreamingResponse:
    """One SSE response forwarding every event of the tenant. The client filters
    by event name (``kds.changed`` / ``floor.changed``) and refetches the matching
    RLS-scoped endpoint — the stream carries no data, so isolation stays in RLS.
    The client loads initial data via its own query, so there is no initial nudge.
    """
    sub = bus.subscribe(tenant_id)

    async def gen() -> AsyncIterator[str]:
        try:
            while True:
                try:
                    event = await asyncio.wait_for(sub.get(), timeout=heartbeat)
                except TimeoutError:
                    yield ": ping\n\n"  # keep proxies from closing the connection
                    continue
                yield f"event: {event.type}\ndata: {json.dumps(event.payload)}\n\n"
        finally:
            sub.close()

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/kds/stream")
@inject
async def kds_stream(
    token: str,
    tokens: TokenService = Depends(Provide[Container.token_service]),
    bus: EventBus = Depends(Provide[Container.event_bus]),
    config: Settings = Depends(Provide[Container.config]),
) -> StreamingResponse:
    tenant_id = tokens.decode_stream_token(token)  # InvalidToken/ExpiredToken → 401
    return _sse_response(bus, tenant_id, config.realtime_heartbeat_s)


@router.get("/floor/stream")
@inject
async def floor_stream(
    token: str,
    tokens: TokenService = Depends(Provide[Container.token_service]),
    bus: EventBus = Depends(Provide[Container.event_bus]),
    config: Settings = Depends(Provide[Container.config]),
) -> StreamingResponse:
    tenant_id = tokens.decode_stream_token(token)
    return _sse_response(bus, tenant_id, config.realtime_heartbeat_s)
