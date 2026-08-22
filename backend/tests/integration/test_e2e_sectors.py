"""End-to-end checks for sectors (salon zones) + assigning them to tables."""

from __future__ import annotations

from tests.integration.test_e2e_auth import _onboard_verify_login


def _auth(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def _row(response, table_id: str) -> dict:
    assert response.status_code == 200, response.text
    return next(r for r in response.json() if r["id"] == table_id)


async def test_sector_crud_and_table_assignment(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="resto", email="owner@resto.com")
    h = _auth(tokens)

    # No sectors to start.
    assert (await http.get("/api/v1/sectors", headers=h)).json() == []

    # Create two, listed by sort_order.
    terraza = await http.post(
        "/api/v1/sectors", json={"name": "Terraza", "color": "#0af", "sort_order": 2}, headers=h
    )
    assert terraza.status_code == 201, terraza.text
    terraza_id = terraza.json()["id"]
    salon = await http.post(
        "/api/v1/sectors", json={"name": "Salón", "sort_order": 1}, headers=h
    )
    salon_id = salon.json()["id"]
    listed = (await http.get("/api/v1/sectors", headers=h)).json()
    assert [s["name"] for s in listed] == ["Salón", "Terraza"]  # sort_order 1, 2

    # Assign a table to a sector + capacity (PATCH is partial).
    table_id = (
        await http.post("/api/v1/tables", json={"number": 4, "name": None}, headers=h)
    ).json()["table_id"]
    patched = await http.patch(
        f"/api/v1/tables/{table_id}",
        json={"sector_id": terraza_id, "capacity": 6},
        headers=h,
    )
    assert patched.status_code == 200, patched.text
    assert patched.json()["sector_id"] == terraza_id
    assert patched.json()["capacity"] == 6

    # The floor row carries the sector + capacity (so free tables group too).
    row = _row(await http.get("/api/v1/floor", headers=h), table_id)
    assert row["sector_id"] == terraza_id
    assert row["capacity"] == 6

    # Capacity becomes the PAX default when the visit opens.
    await http.post("/api/v1/orders", json={"table_id": table_id}, headers=h)
    assert _row(await http.get("/api/v1/floor", headers=h), table_id)["session"]["pax"] == 6

    # Rename a sector.
    renamed = await http.put(
        f"/api/v1/sectors/{salon_id}",
        json={"name": "Interior", "sort_order": 1},
        headers=h,
    )
    assert renamed.status_code == 200, renamed.text
    assert renamed.json()["name"] == "Interior"

    # Delete a sector → gone from the list (the table keeps a harmless dangling id).
    deleted = await http.delete(f"/api/v1/sectors/{terraza_id}", headers=h)
    assert deleted.status_code == 204, deleted.text
    remaining = (await http.get("/api/v1/sectors", headers=h)).json()
    assert [s["name"] for s in remaining] == ["Interior"]


async def test_patch_table_clears_sector(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="bar", email="owner@bar.com")
    h = _auth(tokens)
    sector_id = (
        await http.post("/api/v1/sectors", json={"name": "Barra"}, headers=h)
    ).json()["id"]
    table_id = (
        await http.post("/api/v1/tables", json={"number": 1, "name": None}, headers=h)
    ).json()["table_id"]

    await http.patch(f"/api/v1/tables/{table_id}", json={"sector_id": sector_id}, headers=h)
    # Sending null clears it; omitting capacity leaves it untouched.
    cleared = await http.patch(
        f"/api/v1/tables/{table_id}", json={"sector_id": None}, headers=h
    )
    assert cleared.status_code == 200, cleared.text
    assert cleared.json()["sector_id"] is None


async def test_sector_not_found(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(http, fake_email, slug="caf", email="owner@caf.com")
    h = _auth(tokens)
    missing = await http.put(
        "/api/v1/sectors/00000000-0000-0000-0000-000000000000",
        json={"name": "X", "sort_order": 0},
        headers=h,
    )
    assert missing.status_code == 404
    assert missing.json()["code"] == "sector_not_found"
