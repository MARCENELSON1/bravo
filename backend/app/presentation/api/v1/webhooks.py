"""Public gateway webhooks. No user token: authenticity comes from the signature.

MercadoPago posts ``?data.id=<payment_id>&type=payment`` (and may repeat the id
in the JSON body). We verify the ``x-signature`` HMAC, then the use case fetches
the authoritative status and settles the payment idempotently.
"""

from __future__ import annotations

from typing import Annotated

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Header, Query, Request

from app.application.payment.use_cases import ConfirmGatewayPayment
from app.container import Container

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def _parse_signature(x_signature: str | None) -> tuple[str | None, str]:
    """Split ``ts=<timestamp>,v1=<hmac>`` into (ts, v1)."""
    ts: str | None = None
    received = ""
    if x_signature:
        for part in x_signature.split(","):
            key, _, value = part.strip().partition("=")
            if key == "ts":
                ts = value
            elif key == "v1":
                received = value
    return ts, received


@router.post("/mercadopago")
@inject
async def mercadopago_webhook(
    request: Request,
    data_id: Annotated[str | None, Query(alias="data.id")] = None,
    user_id: Annotated[str | None, Query()] = None,
    x_signature: Annotated[str | None, Header()] = None,
    x_request_id: Annotated[str | None, Header()] = None,
    use_case: ConfirmGatewayPayment = Depends(Provide[Container.confirm_gateway_payment]),
) -> dict[str, str]:
    if data_id is None or user_id is None:
        try:
            body = await request.json()
        except Exception:
            body = None
        if isinstance(body, dict):
            inner = body.get("data")
            if data_id is None and isinstance(inner, dict) and inner.get("id") is not None:
                data_id = str(inner["id"])
            if user_id is None and body.get("user_id") is not None:
                user_id = str(body["user_id"])
    ts, received_hmac = _parse_signature(x_signature)
    # user_id (the seller's MercadoPago id) routes to the tenant's own token.
    await use_case.execute(
        data_id=data_id,
        request_id=x_request_id,
        ts=ts,
        received_hmac=received_hmac,
        account_id=user_id,
    )
    return {"status": "ok"}
