"""Adapter de Twenty CRM: el lead de la landing entra como `person`.

Twenty no tiene campo de texto libre en `people`, así que el mensaje del
formulario se adjunta como `note` vinculada al contacto.

Criterio de fallos, a propósito distinto por paso:
  * si falla la creación del contacto, se propaga → el visitante ve un error
    real en vez de un "te contactamos" que nunca se cumple;
  * si falla la nota, el contacto YA quedó registrado: se loguea y se sigue,
    porque perder el mensaje es mucho menos grave que perder el lead.

Todo lead se loguea a INFO antes de salir, así queda rastro en los logs aunque
el CRM esté caído. La API key nunca se loguea.
"""

from __future__ import annotations

import logging

import httpx

from app.domain.marketing.entities import Lead
from app.domain.marketing.exceptions import LeadNotDelivered
from app.domain.marketing.ports import LeadGateway

logger = logging.getLogger("app.marketing")

_TIMEOUT = 10.0


def _split_name(name: str | None) -> tuple[str, str]:
    """Twenty separa nombre y apellido; la landing pide un campo solo."""
    if not name:
        return "", ""
    parts = name.split()
    return parts[0], " ".join(parts[1:])


class TwentyLeadGateway(LeadGateway):
    def __init__(
        self,
        base_url: str,
        api_key: str,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._transport = transport

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self._base_url,
            transport=self._transport,
            headers={"Authorization": f"Bearer {self._api_key}"},
            timeout=_TIMEOUT,
        )

    async def submit(self, lead: Lead) -> None:
        logger.info("[lead] recibido email=%s nombre=%s", lead.email, lead.name or "-")
        first, last = _split_name(lead.name)
        async with self._client() as client:
            try:
                response = await client.post(
                    "/rest/people",
                    json={
                        "name": {"firstName": first, "lastName": last},
                        "emails": {"primaryEmail": lead.email},
                        "position": "first",
                    },
                )
            except httpx.HTTPError as exc:
                logger.error("[lead] no se pudo contactar a Twenty: %s", exc)
                raise LeadNotDelivered() from exc
            if response.status_code >= 400:
                logger.error(
                    "[lead] Twenty rechazó el contacto (%s): %s",
                    response.status_code,
                    response.text[:300],
                )
                raise LeadNotDelivered()

            person_id = _person_id(response)
            logger.info("[lead] contacto creado en Twenty id=%s", person_id or "?")

            if lead.message and person_id:
                await self._attach_note(client, person_id, lead)

    async def _attach_note(self, client: httpx.AsyncClient, person_id: str, lead: Lead) -> None:
        """Best-effort: el contacto ya existe, el mensaje es un extra."""
        try:
            created = await client.post(
                "/rest/notes",
                json={
                    "title": "Consulta desde la landing",
                    "bodyV2": {"markdown": lead.message},
                    "position": "first",
                },
            )
            note_id = _record_id(created, "note")
            if created.status_code >= 400 or not note_id:
                logger.warning("[lead] no se pudo crear la nota: %s", created.text[:200])
                return
            # El campo es targetPersonId, no personId: con personId Twenty
            # responde 400 y la nota queda huérfana.
            linked = await client.post(
                "/rest/noteTargets",
                json={"noteId": note_id, "targetPersonId": person_id, "position": "first"},
            )
            if linked.status_code >= 400:
                logger.warning("[lead] nota creada pero sin vincular: %s", linked.text[:200])
        except httpx.HTTPError as exc:
            logger.warning("[lead] falló el adjunto de la nota: %s", exc)


def _person_id(response: httpx.Response) -> str | None:
    return _record_id(response, "person")


def _record_id(response: httpx.Response, key: str) -> str | None:
    try:
        payload = response.json()
    except ValueError:
        return None
    data = payload.get("data") or {}
    record = data.get(f"create{key.capitalize()}") or data.get(key) or data
    if isinstance(record, dict):
        value = record.get("id")
        return str(value) if value else None
    return None
