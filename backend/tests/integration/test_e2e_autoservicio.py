"""End-to-end Self-service (Carta QR F3, Fase 3): the diner pays first.

An order placed in Self-service mode is held off the kitchen (source
CUSTOMER_QR_PREPAID, items PENDING) and does NOT show in the "QR por confirmar"
tray. Only when the payment webhook confirms does it march (SENT) and auto-assign
a clocked-in waiter — never marked PAID, so the kitchen lifecycle stays alive.
"""

from __future__ import annotations

from tests.integration.test_e2e_auth import (
    _login,
    _onboard_verify_login,
    _token_from_link,
)
from tests.integration.test_e2e_payments import _auth
from tests.integration.test_e2e_self_order import _product, _qr_token
from tests.integration.test_e2e_table_pay import _enable_self_pay
from tests.integration.test_e2e_webhook import _HOOK, _SIG, mp_client  # noqa: F401

_NIL = "00000000-0000-0000-0000-000000000000"


async def _set_mode(http, h, mode: str) -> None:
    res = await http.put("/api/v1/self-order/settings", json={"mode": mode}, headers=h)
    assert res.status_code == 200, res.text
    assert res.json()["mode"] == mode


async def _clock_in_waiter(http, fake_email, h) -> tuple[dict, str]:
    """Invite + accept + login + clock-in a WAITER. Returns (waiter_auth, waiter_id)."""
    inv = await http.post(
        "/api/v1/users/invite",
        json={"email": "w@resto.com", "role": "WAITER"},
        headers=h,
    )
    assert inv.status_code == 201, inv.text
    token = _token_from_link(fake_email.last().link)
    acc = await http.post(
        "/api/v1/users/accept-invitation",
        json={"token": token, "password": "WaiterPass1!"},
    )
    assert acc.status_code == 200, acc.text
    wauth = _auth(await _login(http, slug="resto", email="w@resto.com", password="WaiterPass1!"))
    cin = await http.post("/api/v1/timeclock/clock-in", json={}, headers=wauth)
    assert cin.status_code in (200, 201), cin.text
    waiter_id = (await http.get("/api/v1/me", headers=wauth)).json()["user_id"]
    return wauth, waiter_id


async def _submit(http, token, pid) -> dict:
    res = await http.post(
        "/api/v1/public/table/order",
        json={"token": token, "lines": [{"product_id": pid, "quantity": 1}]},
    )
    assert res.status_code == 200, res.text
    return res.json()


async def test_selfservice_holds_then_pay_marches_and_assigns(mp_client):  # noqa: F811
    http, fake_email, _ = mp_client
    h = _auth(await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com"))
    _, waiter_id = await _clock_in_waiter(http, fake_email, h)

    pid = await _product(http, h, "Pizza", 1200000)
    await _set_mode(http, h, "SELF_SERVICE")
    await _enable_self_pay(http, h, tips_enabled=False)
    token = await _qr_token(http, h, 21)

    # 1) submit → RETENIDA (OPEN, prepay), NO en la bandeja "QR por confirmar"
    body = await _submit(http, token, pid)
    assert body["status"] == "OPEN"
    assert body["prepay_required"] is True
    order_id = body["order_id"]
    assert (await http.get("/api/v1/orders/pending-qr", headers=h)).json() == []

    # 2) pagar → PENDING (checkout link); todavía NO marcha
    pay = await http.post("/api/v1/public/table/pay", json={"token": token})
    assert pay.status_code == 200, pay.text
    assert pay.json()["checkout_url"]
    assert (await http.get(f"/api/v1/orders/{order_id}", headers=h)).json()["status"] == "OPEN"

    # 3) webhook confirma → MARCHA (SENT, no PAID) + auto-asigna al mozo fichado
    hook = await http.post(_HOOK, headers=_SIG)
    assert hook.status_code == 200, hook.text
    got = (await http.get(f"/api/v1/orders/{order_id}", headers=h)).json()
    assert got["status"] == "SENT"
    assert got["waiter_id"] == waiter_id


async def test_selfservice_without_clocked_in_waiter_marches_orphan(mp_client):  # noqa: F811
    http, fake_email, _ = mp_client
    h = _auth(await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com"))

    pid = await _product(http, h, "Pizza", 1200000)
    await _set_mode(http, h, "SELF_SERVICE")
    await _enable_self_pay(http, h, tips_enabled=False)
    token = await _qr_token(http, h, 22)

    order_id = (await _submit(http, token, pid))["order_id"]
    await http.post("/api/v1/public/table/pay", json={"token": token})
    hook = await http.post(_HOOK, headers=_SIG)
    assert hook.status_code == 200, hook.text

    got = (await http.get(f"/api/v1/orders/{order_id}", headers=h)).json()
    assert got["status"] == "SENT"       # marchó igual (el comensal ya pagó)
    assert got["waiter_id"] == _NIL      # huérfana → un mozo la toma con /claim
