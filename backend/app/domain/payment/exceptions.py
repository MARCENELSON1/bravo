from __future__ import annotations

from app.domain.errors import DomainError


class PaymentNotFound(DomainError):
    code = "payment_not_found"
    message = "No encontramos el pago indicado."


class InvalidPaymentAmount(DomainError):
    code = "invalid_payment_amount"
    message = "El monto del pago debe ser mayor a cero."


class PaymentNotRefundable(DomainError):
    code = "payment_not_refundable"
    message = "Solo se puede reembolsar un pago confirmado."


class InvalidWebhookSignature(DomainError):
    code = "invalid_webhook_signature"
    message = "La firma de la notificación no es válida."


class PaymentGatewayNotConnected(DomainError):
    code = "payment_gateway_not_connected"
    message = "El local no tiene MercadoPago conectado. Conectalo en Integraciones."


class InvalidOAuthState(DomainError):
    code = "invalid_oauth_state"
    message = "El pedido de conexión no es válido o expiró."


class SelfPayDisabled(DomainError):
    code = "self_pay_disabled"
    message = "El local no habilitó el pago desde la mesa."


class NothingToPay(DomainError):
    code = "nothing_to_pay"
    message = "No hay nada para pagar en esta mesa."


class PaymentInProgress(DomainError):
    """Lo que falta cobrar está tomado por un pago en curso (cuenta dividida).

    Aparte de ``NothingToPay`` a propósito: decirle "no hay nada para pagar" a
    alguien cuya parte está siendo pagada por otro lo manda a irse sin pagar.
    """

    code = "payment_in_progress"
    message = "Alguien está pagando esta cuenta ahora. Esperá un momento y volvé a intentar."
