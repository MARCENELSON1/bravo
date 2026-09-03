"""FcmPushService (Fase 4) con un transport fake de httpx: arma el request a FCM
correcto, y purga el token muerto (UNREGISTERED). No pega a la red."""

from __future__ import annotations

import json

import httpx
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from app.domain.notification.entities import DeviceToken
from app.domain.notification.ports import PushMessage
from app.infrastructure.notification.fcm_service import FcmPushService


def _service_account_json(tmp_path) -> str:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()
    path = tmp_path / "sa.json"
    path.write_text(
        json.dumps(
            {
                "client_email": "fcm@wellnod-eccfd.iam.gserviceaccount.com",
                "private_key": pem,
                "token_uri": "https://oauth2.googleapis.com/token",
                "project_id": "wellnod-eccfd",
            }
        )
    )
    return str(path)


class _FakeDevices:
    def __init__(self, tokens: list[DeviceToken]) -> None:
        self._tokens = tokens
        self.deleted: list[str] = []

    async def list_for_user(self, tenant_id: str, user_id: str) -> list[DeviceToken]:
        return self._tokens

    async def register(self, token: DeviceToken) -> None:  # pragma: no cover
        pass

    async def delete(self, tenant_id: str, token: str) -> None:
        self.deleted.append(token)


def _device(token: str) -> DeviceToken:
    return DeviceToken(
        id="d1", tenant_id="t1", user_id="w1", token=token, platform="ios"
    )


def _service(devices: _FakeDevices, tmp_path, handler) -> FcmPushService:
    return FcmPushService(
        device_tokens=devices,  # type: ignore[arg-type]
        credentials_path=_service_account_json(tmp_path),
        transport=httpx.MockTransport(handler),
    )


async def test_sends_fcm_message(tmp_path) -> None:
    sends: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "oauth2.googleapis.com":
            return httpx.Response(200, json={"access_token": "at-1", "expires_in": 3600})
        sends.append(request)
        return httpx.Response(200, json={"name": "projects/x/messages/1"})

    devices = _FakeDevices([_device("tok-abc")])
    svc = _service(devices, tmp_path, handler)
    await svc.notify_user(
        tenant_id="t1",
        user_id="w1",
        message=PushMessage(title="Mesa 7 lista", body="Lista", data={"order_id": "o1"}),
    )

    assert len(sends) == 1
    body = json.loads(sends[0].content)
    assert body["message"]["token"] == "tok-abc"
    assert body["message"]["notification"]["title"] == "Mesa 7 lista"
    assert body["message"]["data"] == {"order_id": "o1"}
    assert devices.deleted == []


async def test_prunes_dead_token(tmp_path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "oauth2.googleapis.com":
            return httpx.Response(200, json={"access_token": "at-1", "expires_in": 3600})
        return httpx.Response(404, json={"error": {"status": "UNREGISTERED"}})

    devices = _FakeDevices([_device("dead-tok")])
    svc = _service(devices, tmp_path, handler)
    await svc.notify_user(
        tenant_id="t1", user_id="w1", message=PushMessage(title="x", body="y")
    )
    assert devices.deleted == ["dead-tok"]


async def test_no_devices_is_noop(tmp_path) -> None:
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(200, json={})

    svc = _service(_FakeDevices([]), tmp_path, handler)
    await svc.notify_user(
        tenant_id="t1", user_id="w1", message=PushMessage(title="x", body="y")
    )
    assert calls == []  # sin devices, ni siquiera pide el token OAuth


async def test_send_failure_never_raises(tmp_path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom")

    svc = _service(_FakeDevices([_device("tok")]), tmp_path, handler)
    # No debe propagar: un push roto no puede romper el flujo de la comanda.
    await svc.notify_user(
        tenant_id="t1", user_id="w1", message=PushMessage(title="x", body="y")
    )
