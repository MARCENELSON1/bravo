"""Process-wide cache of zeep SOAP clients (AFIP WSAA / WSFEv1).

Building a ``zeep.Client`` downloads and parses the service's WSDL. Doing that
on every login and every CAE request re-fetched a document that changes maybe
once a year, adding a network round-trip and a chunk of XML parsing to each
invoice — inside a worker thread, so it also tied up a slot of the executor
shared with the rest of the app.

Clients are cached per WSDL URL. The lock is a ``threading.Lock`` rather than an
``asyncio`` one because callers reach this from ``asyncio.to_thread``: the
contention to guard against is between worker threads, not coroutines.
"""

from __future__ import annotations

import threading

from zeep import Client

_clients: dict[str, Client] = {}
_lock = threading.Lock()


def soap_client(wsdl: str) -> Client:
    """The cached client for ``wsdl``, building it once on first use.

    zeep clients are safe to reuse across calls; the per-request state lives in
    the operation call, not in the client.
    """
    client = _clients.get(wsdl)
    if client is not None:
        return client
    with _lock:
        if (client := _clients.get(wsdl)) is not None:  # re-check under the lock
            return client
        client = Client(wsdl)
        _clients[wsdl] = client
        return client


def reset_cache() -> None:
    """Drop every cached client. For tests that stub the WSDL layer."""
    with _lock:
        _clients.clear()
