"""The wiring, end to end: marking a course ready queues the aviso instead of
sending it, and the drainer is what actually delivers it.

The unit tests cover each piece; this one proves they are plugged in — that a
real HTTP request through the real container leaves a row behind.
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from tests.integration.test_e2e_auth import _onboard_verify_login


def _auth(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


async def test_marking_a_course_ready_queues_the_push_instead_of_sending_it(
    client, admin_engine: AsyncEngine
):
    http, fake_email = client
    h = _auth(await _onboard_verify_login(http, fake_email, slug="outbox", email="o@outbox.com"))

    product = await http.post(
        "/api/v1/products",
        json={"name": "Milanesa", "price_amount": 150000, "category": "Platos"},
        headers=h,
    )
    product_id = product.json()["product_id"]
    table = await http.post("/api/v1/tables", json={"number": 7}, headers=h)
    table_id = table.json()["table_id"]

    order_id = (
        await http.post("/api/v1/orders", json={"table_id": table_id}, headers=h)
    ).json()["order_id"]
    await http.post(
        f"/api/v1/orders/{order_id}/items",
        json={"product_id": product_id, "quantity": 2},
        headers=h,
    )
    await http.post(f"/api/v1/orders/{order_id}/send", headers=h)
    await http.post(f"/api/v1/orders/{order_id}/preparing", headers=h)

    assert await _queued(admin_engine) == [], "nothing queued before the plate is ready"

    ready = await http.post(f"/api/v1/orders/{order_id}/ready", headers=h)
    assert ready.status_code == 200, ready.text

    # The push did not go out during the request — it is sitting in the outbox,
    # already rendered, waiting for the worker.
    (task,) = await _queued(admin_engine)
    assert task["kind"] == "PUSH_NOTIFICATION"
    assert task["status"] == "PENDING"
    assert task["payload"]["data"]["order_id"] == order_id
    assert "Mesa 7" in task["payload"]["title"]
    assert "2× Milanesa" in task["payload"]["body"]


async def _queued(engine: AsyncEngine) -> list[dict]:
    """Read the queue with the admin connection: the drainer's own scoping is
    what this test is checking, so it must not depend on it."""
    async with engine.begin() as conn:
        rows = await conn.execute(
            text("SELECT kind, status, payload FROM outbox_tasks ORDER BY created_at")
        )
        return [{"kind": k, "status": s, "payload": p} for k, s, p in rows]
