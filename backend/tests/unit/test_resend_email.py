"""Unit tests for the Resend email adapter (in-process httpx transport)."""

from __future__ import annotations

import json

import httpx
import pytest

from app.infrastructure.email.resend_sender import ResendEmailSender, ResendEmailSendFailed


def _sender(handler) -> ResendEmailSender:
    return ResendEmailSender(
        api_key="re_test_key",
        from_email="Wellnod <no-reply@wellnod.com>",
        transport=httpx.MockTransport(handler),
    )


async def test_verification_posts_expected_payload() -> None:
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["auth"] = request.headers["Authorization"]
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"id": "msg-123"})

    await _sender(handler).send_email_verification(to="dueno@bar.com", link="https://app/x?token=t")

    assert seen["path"] == "/emails"
    assert seen["auth"] == "Bearer re_test_key"
    assert seen["body"]["from"] == "Wellnod <no-reply@wellnod.com>"
    assert seen["body"]["to"] == ["dueno@bar.com"]
    assert seen["body"]["subject"] == "Verificá tu email — Wellnod"
    assert "https://app/x?token=t" in seen["body"]["text"]


async def test_invitation_uses_tenant_name_in_subject() -> None:
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"id": "msg-456"})

    await _sender(handler).send_invitation(
        to="mozo@bar.com", link="https://app/inv", tenant_name="Bar Pepe"
    )

    assert seen["body"]["subject"] == "Te invitaron a Bar Pepe en Wellnod"
    assert "Bar Pepe" in seen["body"]["text"]


async def test_password_reset_sends_reset_copy() -> None:
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"id": "msg-789"})

    await _sender(handler).send_password_reset(to="dueno@bar.com", link="https://app/reset")

    assert seen["body"]["subject"] == "Restablecé tu contraseña — Wellnod"
    assert "https://app/reset" in seen["body"]["text"]


async def test_error_response_raises_with_resend_message() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            403,
            json={
                "statusCode": 403,
                "name": "validation_error",
                "message": "The wellnod.com domain is not verified",
            },
        )

    with pytest.raises(ResendEmailSendFailed) as excinfo:
        await _sender(handler).send_email_verification(to="a@b.com", link="https://app/x")

    assert "403" in str(excinfo.value)
    assert "not verified" in str(excinfo.value)
    # The API key must never leak into the error surface.
    assert "re_test_key" not in str(excinfo.value)


async def test_non_json_error_body_still_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(502, text="upstream boom")

    with pytest.raises(ResendEmailSendFailed) as excinfo:
        await _sender(handler).send_password_reset(to="a@b.com", link="https://app/x")

    assert "502" in str(excinfo.value)
