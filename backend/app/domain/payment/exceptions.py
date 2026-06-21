from __future__ import annotations

from app.domain.errors import DomainError


class PaymentNotFound(DomainError):
    code = "payment_not_found"
    message = "No encontramos el pago indicado."


class InvalidPaymentAmount(DomainError):
    code = "invalid_payment_amount"
    message = "El monto del pago debe ser mayor a cero."


class InvalidWebhookSignature(DomainError):
    code = "invalid_webhook_signature"
    message = "La firma de la notificación no es válida."


class PaymentGatewayNotConnected(DomainError):
    code = "payment_gateway_not_connected"
    message = "El local no tiene MercadoPago conectado. Conectalo en Integraciones."


class InvalidOAuthState(DomainError):
    code = "invalid_oauth_state"
    message = "El pedido de conexión no es válido o expiró."
