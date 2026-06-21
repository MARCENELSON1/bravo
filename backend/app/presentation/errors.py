"""Maps domain exceptions to HTTP responses ``{code, message}`` (code EN, message ES).

Routers and use cases never raise ``HTTPException``; they raise domain errors and
these handlers translate them.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.domain.errors import DomainError
from app.domain.identity.exceptions import (
    ExpiredToken,
    InvalidInvitation,
    InvalidToken,
    TokenAlreadyUsed,
)
from app.domain.order.exceptions import EmptyOrder, InvalidOrderTransition, OrderNotFound
from app.domain.payment.exceptions import (
    InvalidOAuthState,
    InvalidPaymentAmount,
    InvalidWebhookSignature,
    PaymentGatewayNotConnected,
    PaymentNotFound,
)
from app.domain.product.exceptions import InactiveProduct, ProductNotFound
from app.domain.shared.exceptions import (
    CurrencyMismatch,
    InvalidMoneyAmount,
    UnsupportedCurrency,
)
from app.domain.table.exceptions import TableNotFound
from app.domain.tenant.exceptions import TenantAlreadyExists, TenantNotFound
from app.domain.user.exceptions import (
    EmailAlreadyRegistered,
    EmailNotVerified,
    InactiveUser,
    InsufficientRole,
    InvalidCredentials,
    InvalidEmail,
    UserLocked,
    UserNotFound,
)

# Order matters only for readability; lookup uses isinstance against each entry.
_STATUS_BY_TYPE: list[tuple[type[DomainError], int]] = [
    (InvalidCredentials, 401),
    (InvalidToken, 401),
    (ExpiredToken, 401),
    (EmailNotVerified, 403),
    (InactiveUser, 403),
    (InsufficientRole, 403),
    (UserNotFound, 404),
    (TenantNotFound, 404),
    (UserLocked, 423),
    (EmailAlreadyRegistered, 409),
    (TenantAlreadyExists, 409),
    (TokenAlreadyUsed, 409),
    (InvalidInvitation, 400),
    (InvalidEmail, 422),
    # Fase 2 — comandas/productos/mesas + Money
    (TableNotFound, 404),
    (ProductNotFound, 404),
    (OrderNotFound, 404),
    (InactiveProduct, 409),
    (InvalidOrderTransition, 409),
    (EmptyOrder, 422),
    (UnsupportedCurrency, 422),
    (CurrencyMismatch, 422),
    (InvalidMoneyAmount, 422),
    # Fase 3 — pagos
    (PaymentNotFound, 404),
    (InvalidPaymentAmount, 422),
    (InvalidWebhookSignature, 401),
    (PaymentGatewayNotConnected, 409),
    (InvalidOAuthState, 400),
]


def _status_for(exc: DomainError) -> int:
    for klass, status in _STATUS_BY_TYPE:
        if isinstance(exc, klass):
            return status
    return 400


def register_error_handlers(app: FastAPI) -> None:
    async def handle_domain_error(request: Request, exc: Exception) -> JSONResponse:
        assert isinstance(exc, DomainError)
        return JSONResponse(
            status_code=_status_for(exc),
            content={"code": exc.code, "message": exc.message},
        )

    async def handle_validation_error(
        request: Request, exc: Exception
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "code": "validation_error",
                "message": "Los datos enviados no son válidos.",
            },
        )

    app.add_exception_handler(DomainError, handle_domain_error)
    app.add_exception_handler(RequestValidationError, handle_validation_error)
