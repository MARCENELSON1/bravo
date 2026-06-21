"""WSAA (AFIP) — obtains and caches a Ticket de Acceso (TA).

The Login Ticket Request is signed as a CMS/PKCS#7 message with the tenant's
X.509 certificate (equivalent to ``openssl cms -sign -nodetach -outform DER``)
and sent to ``LoginCms``. AFIP returns a token+sign valid for ~12 h; we cache it
per CUIT because re-requesting a TA while one is still valid is rejected and
rate-limited by AFIP. All cert/key material stays in memory and is never logged.

This is I/O against AFIP and cannot be unit-tested without homologación
credentials; the pure request/response mapping lives in ``wsfe_mapping``.
"""

from __future__ import annotations

import asyncio
import base64
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from xml.etree import ElementTree as ET

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from cryptography.hazmat.primitives.serialization import pkcs7
from zeep import Client

# WSAA endpoints (homologación vs producción).
_WSAA_WSDL = {
    False: "https://wsaahomo.afip.gov.ar/ws/services/LoginCms?WSDL",
    True: "https://wsaa.afip.gov.ar/ws/services/LoginCms?WSDL",
}
# Service we request the TA for. We only need electronic invoicing (WSFEv1).
_SERVICE = "wsfe"
# Validity window of the Login Ticket Request itself (not the TA).
_LTR_WINDOW = timedelta(minutes=10)
# Renew a bit before the real expiry to avoid edge-of-window rejections.
_RENEW_MARGIN = timedelta(minutes=10)


class AfipAuthError(RuntimeError):
    """WSAA login failed (bad cert/key, AFIP down, or a still-valid TA)."""


class AfipServiceError(RuntimeError):
    """WSFEv1 returned a top-level error (Errors/auth) — not a comprobante reject."""


@dataclass(frozen=True)
class AccessTicket:
    """AFIP Ticket de Acceso: the (token, sign) pair WSFEv1 expects in ``Auth``."""

    token: str
    sign: str
    expires_at: datetime


def _login_ticket_request(now: datetime) -> bytes:
    """Build the unsigned ``loginTicketRequest`` XML."""
    root = ET.Element("loginTicketRequest", {"version": "1.0"})
    header = ET.SubElement(root, "header")
    ET.SubElement(header, "uniqueId").text = str(int(now.timestamp()))
    ET.SubElement(header, "generationTime").text = (now - _LTR_WINDOW).isoformat()
    ET.SubElement(header, "expirationTime").text = (now + _LTR_WINDOW).isoformat()
    ET.SubElement(root, "service").text = _SERVICE
    return ET.tostring(root, encoding="UTF-8")


def _sign_cms(payload: bytes, certificate: str, private_key: str) -> str:
    """Sign ``payload`` as a CMS/PKCS#7 message (DER, base64) — the format
    ``LoginCms`` expects. Data is embedded (non-detached)."""
    cert = x509.load_pem_x509_certificate(certificate.encode())
    key = serialization.load_pem_private_key(private_key.encode(), password=None)
    if not isinstance(key, rsa.RSAPrivateKey | ec.EllipticCurvePrivateKey):
        raise AfipAuthError("AFIP certificate private key must be RSA or EC")
    der = (
        pkcs7.PKCS7SignatureBuilder()
        .set_data(payload)
        .add_signer(cert, key, hashes.SHA256())
        .sign(serialization.Encoding.DER, [pkcs7.PKCS7Options.Binary])
    )
    return base64.b64encode(der).decode()


def _parse_ticket(login_cms_response: str) -> AccessTicket:
    """Extract token/sign/expiration from the ``loginTicketResponse`` XML."""
    root = ET.fromstring(login_cms_response)
    token = root.findtext("credentials/token")
    sign = root.findtext("credentials/sign")
    expiration = root.findtext("header/expirationTime")
    if not token or not sign or not expiration:
        raise AfipAuthError("WSAA response missing token/sign/expirationTime")
    return AccessTicket(token=token, sign=sign, expires_at=datetime.fromisoformat(expiration))


class AfipWsaa:
    """Caches one TA per (CUIT, env) and renews it near expiry. Login is
    serialized by a lock because AFIP rejects a second login while a TA is valid.

    The cache is in-process: a restart loses it and may hit AFIP's "TA ya válido"
    until the current TA expires (~12 h). A DB-backed TA cache would remove that
    edge; out of scope for the MVP.
    """

    def __init__(self) -> None:
        self._cache: dict[tuple[str, bool], AccessTicket] = {}
        self._lock = asyncio.Lock()

    async def access_ticket(
        self, *, cuit: str, certificate: str, private_key: str, production: bool
    ) -> AccessTicket:
        key = (cuit, production)
        if (cached := self._fresh(key)) is not None:
            return cached
        async with self._lock:
            if (cached := self._fresh(key)) is not None:  # re-check under the lock
                return cached
            ticket = await asyncio.to_thread(self._login, certificate, private_key, production)
            self._cache[key] = ticket
            return ticket

    def _fresh(self, key: tuple[str, bool]) -> AccessTicket | None:
        cached = self._cache.get(key)
        if cached is None:
            return None
        if cached.expires_at - _RENEW_MARGIN <= datetime.now(UTC):
            return None
        return cached

    def _login(self, certificate: str, private_key: str, production: bool) -> AccessTicket:
        cms = _sign_cms(_login_ticket_request(datetime.now(UTC)), certificate, private_key)
        client = Client(_WSAA_WSDL[production])
        try:
            response = client.service.loginCms(in0=cms)
        except Exception as exc:  # zeep faults / transport errors
            raise AfipAuthError(f"WSAA loginCms failed: {exc}") from exc
        return _parse_ticket(response)
