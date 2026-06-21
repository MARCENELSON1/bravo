"""End-to-end fichaje (shifts) flow over HTTP against the real app + DB."""

from __future__ import annotations

from tests.integration.test_e2e_auth import _onboard_verify_login


def _auth(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


async def test_clock_in_out_and_list(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    h = _auth(tokens)

    cin = await http.post("/api/v1/timeclock/clock-in", json={}, headers=h)
    assert cin.status_code == 201, cin.text
    assert cin.json()["status"] == "OPEN"
    assert cin.json()["source"] == "SELF"
    assert cin.json()["worked_minutes"] is None

    me_open = await http.get("/api/v1/timeclock/me", headers=h)
    assert me_open.json()["open_shift"] is not None

    cout = await http.post("/api/v1/timeclock/clock-out", headers=h)
    assert cout.status_code == 200, cout.text
    assert cout.json()["status"] == "CLOSED"
    assert cout.json()["worked_minutes"] is not None and cout.json()["worked_minutes"] >= 0

    me_closed = await http.get("/api/v1/timeclock/me", headers=h)
    assert me_closed.json()["open_shift"] is None
    assert len(me_closed.json()["recent"]) == 1

    shifts = await http.get("/api/v1/timeclock/shifts", headers=h)
    assert shifts.status_code == 200
    assert len(shifts.json()) == 1


async def test_double_clock_in_rejected(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    h = _auth(tokens)
    await http.post("/api/v1/timeclock/clock-in", json={}, headers=h)
    again = await http.post("/api/v1/timeclock/clock-in", json={}, headers=h)
    assert again.status_code == 409
    assert again.json()["code"] == "shift_already_open"


async def test_clock_out_without_open_rejected(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    h = _auth(tokens)
    out = await http.post("/api/v1/timeclock/clock-out", headers=h)
    assert out.status_code == 409
    assert out.json()["code"] == "no_open_shift"


async def test_punch_toggles(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    h = _auth(tokens)
    first = await http.post("/api/v1/timeclock/punch", headers=h)
    assert first.json()["status"] == "OPEN"
    second = await http.post("/api/v1/timeclock/punch", headers=h)
    assert second.json()["status"] == "CLOSED"
    assert second.json()["id"] == first.json()["id"]


async def test_manager_adjust_shift(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    h = _auth(tokens)
    cin = await http.post("/api/v1/timeclock/clock-in", json={}, headers=h)
    await http.post("/api/v1/timeclock/clock-out", headers=h)
    shift_id = cin.json()["id"]

    patched = await http.patch(
        f"/api/v1/timeclock/shifts/{shift_id}",
        json={
            "clock_in_at": "2026-06-21T09:00:00+00:00",
            "clock_out_at": "2026-06-21T17:00:00+00:00",
        },
        headers=h,
    )
    assert patched.status_code == 200, patched.text
    body = patched.json()
    assert body["source"] == "MANAGER"
    assert body["adjusted_by"] is not None
    assert body["worked_minutes"] == 480


async def test_adjust_invalid_time_rejected(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com")
    h = _auth(tokens)
    cin = await http.post("/api/v1/timeclock/clock-in", json={}, headers=h)
    shift_id = cin.json()["id"]
    bad = await http.patch(
        f"/api/v1/timeclock/shifts/{shift_id}",
        json={
            "clock_in_at": "2026-06-21T17:00:00+00:00",
            "clock_out_at": "2026-06-21T09:00:00+00:00",
        },
        headers=h,
    )
    assert bad.status_code == 422
    assert bad.json()["code"] == "invalid_shift_time"


async def test_timeclock_rls_isolation(client):
    http, fake_email = client
    t1 = await _onboard_verify_login(http, fake_email, slug="uno", email="a@uno.com")
    await http.post("/api/v1/timeclock/clock-in", json={}, headers=_auth(t1))
    t2 = await _onboard_verify_login(http, fake_email, slug="dos", email="b@dos.com")
    assert (await http.get("/api/v1/timeclock/shifts", headers=_auth(t2))).json() == []
