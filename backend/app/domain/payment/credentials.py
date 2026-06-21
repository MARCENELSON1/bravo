from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class PaymentProvider(StrEnum):
    MERCADOPAGO = "MERCADOPAGO"


class ConnectionStatus(StrEnum):
    CONNECTED = "CONNECTED"
    DISCONNECTED = "DISCONNECTED"


@dataclass
class PaymentCredential:
    """A tenant's connection to a payment provider (its own MercadoPago account).

    Tokens are stored **encrypted at rest** (the repo cibers/deciphers via a
    ``TokenCipher``); in memory they are plaintext. ``external_account_id`` is the
    seller's MercadoPago ``user_id`` — used to route inbound webhooks back to the
    tenant. ``live_mode`` is False for sandbox (TEST) credentials.
    """

    id: str
    tenant_id: str
    provider: PaymentProvider
    external_account_id: str
    access_token: str
    refresh_token: str | None = None
    public_key: str | None = None
    nickname: str | None = None
    expires_at: datetime | None = None
    live_mode: bool = False
    status: ConnectionStatus = ConnectionStatus.CONNECTED
    created_at: datetime | None = None
    updated_at: datetime | None = None
