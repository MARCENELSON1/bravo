"""End-to-end reservations flow over HTTP against the real app + DB."""

from __future__ import annotations

from tests.integration.test_e2e_auth import _onboard_verify_login


def _auth(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


async def _new_reservation(http, h, **overrides) -> dict:
    body = {
        "customer_name": "Pérez",
        "party_size": 2,
        "reserved_at": "2026-06-21T21:00:00+00:00",
        "turn": "DINNER",
        "customer_phone": "351-555-0000",
    }
    body.update(overrides)
    resp = await http.post("/api/v1/reservations", json=body, headers=h)
    assert resp.status_code == 201, resp.text
    return resp.json()


async def test_create_confirm_seat_complete(client):
    http, fake_email = client
    h = _auth(await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com"))
    rid = (await _new_reservation(http, h))["reservation_id"]

    confirmed = await http.post(f"/api/v1/reservations/{rid}/confirm", headers=h)
    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.json()["status"] == "CONFIRMED"

    seated = await http.post(f"/api/v1/reservations/{rid}/seat", headers=h)
    assert seated.json()["status"] == "SEATED"

    completed = await http.post(f"/api/v1/reservations/{rid}/complete", headers=h)
    assert completed.json()["status"] == "COMPLETED"


async def test_mark_no_show(client):
    http, fake_email = client
    h = _auth(await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com"))
    rid = (await _new_reservation(http, h))["reservation_id"]
    await http.post(f"/api/v1/reservations/{rid}/confirm", headers=h)
    no_show = await http.post(f"/api/v1/reservations/{rid}/no-show", headers=h)
    assert no_show.status_code == 200
    assert no_show.json()["status"] == "NO_SHOW"


async def test_invalid_transition_rejected(client):
    http, fake_email = client
    h = _auth(await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com"))
    rid = (await _new_reservation(http, h))["reservation_id"]
    await http.post(f"/api/v1/reservations/{rid}/cancel", headers=h)
    # Completing a cancelled reservation is illegal.
    bad = await http.post(f"/api/v1/reservations/{rid}/complete", headers=h)
    assert bad.status_code == 409
    assert bad.json()["code"] == "invalid_reservation_transition"


async def test_reservation_with_table(client):
    http, fake_email = client
    h = _auth(await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com"))
    table = await http.post("/api/v1/tables", json={"number": 5, "name": None}, headers=h)
    table_id = table.json()["table_id"]
    created = await _new_reservation(http, h, table_id=table_id)
    got = await http.get(f"/api/v1/reservations/{created['reservation_id']}", headers=h)
    assert got.json()["table_id"] == table_id


async def test_reservation_unknown_table_404(client):
    http, fake_email = client
    h = _auth(await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com"))
    resp = await http.post(
        "/api/v1/reservations",
        json={
            "customer_name": "Pérez",
            "party_size": 2,
            "reserved_at": "2026-06-21T21:00:00+00:00",
            "turn": "DINNER",
            "table_id": "00000000-0000-0000-0000-000000000000",
        },
        headers=h,
    )
    assert resp.status_code == 404
    assert resp.json()["code"] == "table_not_found"


async def test_update_reschedules(client):
    http, fake_email = client
    h = _auth(await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com"))
    rid = (await _new_reservation(http, h))["reservation_id"]
    patched = await http.patch(
        f"/api/v1/reservations/{rid}",
        json={
            "party_size": 4,
            "reserved_at": "2026-06-22T13:00:00+00:00",
            "turn": "LUNCH",
        },
        headers=h,
    )
    assert patched.status_code == 200, patched.text
    body = patched.json()
    assert body["party_size"] == 4
    assert body["turn"] == "LUNCH"


async def test_agenda_filters_by_day_and_turn(client):
    http, fake_email = client
    h = _auth(await _onboard_verify_login(http, fake_email, slug="resto", email="o@resto.com"))
    await _new_reservation(http, h, reserved_at="2026-06-21T13:00:00+00:00", turn="LUNCH")
    await _new_reservation(http, h, reserved_at="2026-06-21T21:00:00+00:00", turn="DINNER")
    await _new_reservation(http, h, reserved_at="2026-06-22T21:00:00+00:00", turn="DINNER")

    # Day filter: only the two on the 21st.
    day = await http.get(
        "/api/v1/reservations?from=2026-06-21T00:00:00%2B00:00&to=2026-06-21T23:59:59%2B00:00",
        headers=h,
    )
    assert day.status_code == 200
    assert len(day.json()) == 2

    # Turn filter on top of the day.
    dinner = await http.get(
        "/api/v1/reservations?from=2026-06-21T00:00:00%2B00:00&to=2026-06-21T23:59:59%2B00:00&turn=DINNER",
        headers=h,
    )
    assert len(dinner.json()) == 1
    assert dinner.json()[0]["turn"] == "DINNER"


async def test_reservations_rls_isolation(client):
    http, fake_email = client
    t1 = await _onboard_verify_login(http, fake_email, slug="uno", email="a@uno.com")
    await _new_reservation(http, _auth(t1))
    t2 = await _onboard_verify_login(http, fake_email, slug="dos", email="b@dos.com")
    assert (await http.get("/api/v1/reservations", headers=_auth(t2))).json() == []
