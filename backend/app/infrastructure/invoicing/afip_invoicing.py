"""AFIP electronic invoicing adapter (WSFEv1) behind the ``ElectronicInvoicing``
port. Per request it resolves the tenant's credentials, gets a TA via WSAA, asks
WSFEv1 for the next authorised number and then the CAE. SOAP I/O runs in a
thread (``zeep`` is sync). A comprobante rejection (``Resultado='R'``) comes back
as ``CaeResult(authorized=False, ...)`` so the use case records it; auth/transport
failures raise.

Untestable without homologación credentials; the request/response field mapping
is unit-tested in ``wsfe_mapping``/``test_wsfe_mapping``.
"""

from __future__ import annotations

import asyncio
from datetime import date, datetime
from typing import Any

from zeep import Client

from app.domain.invoice.entities import Invoice
from app.domain.invoice.ports import CaeResult, ElectronicInvoicing, TaxCredentialsResolver
from app.infrastructure.invoicing.afip_wsaa import (
    AccessTicket,
    AfipServiceError,
    AfipWsaa,
)
from app.infrastructure.invoicing.wsfe_mapping import build_cae_request, cbte_tipo

# WSFEv1 endpoints (homologación vs producción).
_WSFE_WSDL = {
    False: "https://wswhomo.afip.gov.ar/wsfev1/service.asmx?WSDL",
    True: "https://servicios1.afip.gov.ar/wsfev1/service.asmx?WSDL",
}


class AfipInvoicing(ElectronicInvoicing):
    def __init__(
        self,
        *,
        resolver: TaxCredentialsResolver,
        wsaa: AfipWsaa | None = None,
        afip_env: str = "homo",
    ) -> None:
        self._resolver = resolver
        self._wsaa = wsaa or AfipWsaa()
        # App-level kill-switch to force prod; per-tenant ``live_mode`` is the
        # normal source of truth (homologación tenants stay on the homo URLs).
        self._force_prod = afip_env == "prod"

    async def authorize(self, *, invoice: Invoice) -> CaeResult:
        creds = await self._resolver.for_tenant(invoice.tenant_id)
        production = creds.live_mode or self._force_prod
        ticket = await self._wsaa.access_ticket(
            cuit=creds.cuit,
            certificate=creds.certificate,
            private_key=creds.private_key,
            production=production,
        )
        return await asyncio.to_thread(
            self._request_cae, invoice, creds.cuit, creds.point_of_sale, ticket, production
        )

    def _request_cae(
        self, invoice: Invoice, cuit: str, pto_vta: int, ticket: AccessTicket, production: bool
    ) -> CaeResult:
        client = Client(_WSFE_WSDL[production])
        auth = {"Token": ticket.token, "Sign": ticket.sign, "Cuit": int(cuit)}
        tipo = cbte_tipo(invoice.type)

        last = client.service.FECompUltimoAutorizado(Auth=auth, PtoVta=pto_vta, CbteTipo=tipo)
        if (errors := _errors(last)) is not None:
            raise AfipServiceError(f"FECompUltimoAutorizado: {errors}")
        number = int(last.CbteNro) + 1

        det = build_cae_request(invoice, number, date.today().strftime("%Y%m%d"))
        request = {
            "FeCabReq": {"CantReg": 1, "PtoVta": pto_vta, "CbteTipo": tipo},
            "FeDetReq": {"FECAEDetRequest": [det]},
        }
        response = client.service.FECAESolicitar(Auth=auth, FeCAEReq=request)
        return _to_cae_result(response, number)


def _join(container: Any, list_attr: str) -> str | None:
    """Join AFIP's ``{Code, Msg}`` items (Errors/Err, Observaciones/Obs)."""
    items = getattr(container, list_attr, None) if container else None
    if not items:
        return None
    return "; ".join(f"{i.Code}: {i.Msg}" for i in items)


def _errors(response: Any) -> str | None:
    """Top-level ``Errors`` (auth/structure errors), if any."""
    return _join(getattr(response, "Errors", None), "Err")


def _observations(detail: Any) -> str | None:
    """Per-comprobante ``Observaciones`` (warnings / reject reasons), if any."""
    return _join(getattr(detail, "Observaciones", None), "Obs")


def _to_cae_result(response: Any, number: int) -> CaeResult:
    top = _errors(response)
    details = response.FeDetResp.FECAEDetResponse
    detail = details[0] if isinstance(details, list) else details
    observations = _observations(detail) or top
    if getattr(detail, "Resultado", None) != "A":
        return CaeResult(
            authorized=False, number=None, cae=None, cae_expiration=None, observations=observations
        )
    return CaeResult(
        authorized=True,
        number=number,
        cae=detail.CAE,
        cae_expiration=_parse_yyyymmdd(getattr(detail, "CAEFchVto", None)),
        observations=observations,
    )


def _parse_yyyymmdd(value: str | None) -> date | None:
    return datetime.strptime(value, "%Y%m%d").date() if value else None
