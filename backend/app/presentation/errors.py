"""Maps domain exceptions to HTTP responses ``{code, message}`` (code EN, message ES).

Routers and use cases never raise ``HTTPException``; they raise domain errors and
these handlers translate them.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.domain.advisor.exceptions import InvalidAdvisorSettings
from app.domain.cashier.exceptions import (
    CashSessionAlreadyClosed,
    CashSessionAlreadyOpen,
    CashSessionNotFound,
)
from app.domain.copilot.exceptions import (
    CopilotDisabled,
    CopilotQueryError,
    UnsafeQuery,
)
from app.domain.errors import DomainError
from app.domain.identity.exceptions import (
    ExpiredToken,
    InvalidInvitation,
    InvalidToken,
    TokenAlreadyUsed,
)
from app.domain.inventory.exceptions import (
    IngredientNotFound,
    InvalidQuantity,
    InvalidUnitCost,
    RecipeNotFound,
    SupplierNotFound,
)
from app.domain.invoice.exceptions import (
    InvoiceNotFound,
    OrderNotInvoiceable,
    TaxGatewayNotConnected,
)
from app.domain.order.exceptions import (
    EmptyOrder,
    InvalidItemQuantity,
    InvalidItemTransition,
    InvalidOrderTransition,
    ItemNotFound,
    ItemNotPending,
    OrderNotFound,
)
from app.domain.payment.exceptions import (
    InvalidOAuthState,
    InvalidPaymentAmount,
    InvalidWebhookSignature,
    PaymentGatewayNotConnected,
    PaymentNotFound,
    PaymentNotRefundable,
)
from app.domain.product.exceptions import InactiveProduct, ProductNotFound
from app.domain.reservation.exceptions import (
    InvalidPartySize,
    InvalidReservationTransition,
    ReservationNotFound,
)
from app.domain.shared.exceptions import (
    CurrencyMismatch,
    InvalidMoneyAmount,
    UnsupportedCurrency,
)
from app.domain.table.exceptions import TableNotFound
from app.domain.tenant.exceptions import TenantAlreadyExists, TenantNotFound
from app.domain.timeclock.exceptions import (
    InvalidPresenceDevice,
    InvalidPresenceToken,
    InvalidShiftTime,
    NoOpenShift,
    PresenceDisabled,
    PresenceRateLimited,
    PresenceTokenReused,
    ShiftAlreadyClosed,
    ShiftAlreadyOpen,
    ShiftNotFound,
)
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
    (ItemNotFound, 404),
    (ItemNotPending, 409),
    (InvalidItemTransition, 409),
    (InvalidItemQuantity, 422),
    (UnsupportedCurrency, 422),
    (CurrencyMismatch, 422),
    (InvalidMoneyAmount, 422),
    # Fase 3 — pagos
    (PaymentNotFound, 404),
    (PaymentNotRefundable, 409),
    (InvalidPaymentAmount, 422),
    (InvalidWebhookSignature, 401),
    (PaymentGatewayNotConnected, 409),
    (InvalidOAuthState, 400),
    # Fase 4 — facturación AFIP
    (InvoiceNotFound, 404),
    (OrderNotInvoiceable, 409),
    (TaxGatewayNotConnected, 409),
    # Fase 5 — fichaje
    (ShiftNotFound, 404),
    (ShiftAlreadyOpen, 409),
    (NoOpenShift, 409),
    (ShiftAlreadyClosed, 409),
    (InvalidShiftTime, 422),
    # Fase 5.5 — presencia (QR / código)
    (InvalidPresenceToken, 401),
    (PresenceTokenReused, 409),
    (PresenceRateLimited, 429),
    (InvalidPresenceDevice, 401),
    (PresenceDisabled, 409),
    # Fase 6 — inventario / food cost
    (IngredientNotFound, 404),
    (SupplierNotFound, 404),
    (RecipeNotFound, 404),
    (InvalidQuantity, 422),
    (InvalidUnitCost, 422),
    # Fase 7 — reservas
    (ReservationNotFound, 404),
    (InvalidReservationTransition, 409),
    (InvalidPartySize, 422),
    # Fase 9 — asesor financiero
    (InvalidAdvisorSettings, 422),
    # Fase 14 — caja / arqueo Z
    (CashSessionNotFound, 404),
    (CashSessionAlreadyOpen, 409),
    (CashSessionAlreadyClosed, 409),
    # Fase 11 — copiloto IA
    (CopilotDisabled, 409),
    (UnsafeQuery, 422),
    (CopilotQueryError, 422),
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
