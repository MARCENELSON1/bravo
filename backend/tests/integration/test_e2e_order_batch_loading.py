"""El plano y el KDS hidratan varias comandas con dos queries, no con una por orden.

`SqlAlchemyOrderRepository` traía los ítems de cada orden en su propia consulta
(N+1): con 25 mesas activas, cada poll de cada dispositivo pagaba 25 consultas
de más. Ahora se agrupan en una sola. Es un refactor: lo que se verifica acá es
que el resultado no cambió — todas las órdenes con todos sus ítems, cada una en
el orden en que se cargaron.
"""

from __future__ import annotations

from tests.integration.test_e2e_auth import _onboard_verify_login


def _auth(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


async def test_floor_hydrates_every_order_with_all_its_items_in_order(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(
        http, fake_email, slug="lote", email="owner@lote.com"
    )
    h = _auth(tokens)

    # Tres platos distintos, para poder distinguir el orden de las líneas.
    product_ids = [
        (
            await http.post(
                "/api/v1/products",
                json={"name": name, "price_amount": price, "category": None},
                headers=h,
            )
        ).json()["product_id"]
        for name, price in [("Milanesa", 1000), ("Papas", 500), ("Agua", 300)]
    ]

    # Dos mesas abiertas a la vez, con distinta cantidad de líneas: es el caso
    # que antes disparaba una consulta por comanda.
    expected: dict[str, list[str]] = {}
    for number, line_count in ((1, 3), (2, 2)):
        table_id = (
            await http.post("/api/v1/tables", json={"number": number}, headers=h)
        ).json()["table_id"]
        order_id = (
            await http.post("/api/v1/orders", json={"table_id": table_id}, headers=h)
        ).json()["order_id"]
        for product_id in product_ids[:line_count]:
            response = await http.post(
                f"/api/v1/orders/{order_id}/items",
                json={"product_id": product_id, "quantity": 1},
                headers=h,
            )
            assert response.status_code == 200, response.text
        expected[order_id] = product_ids[:line_count]

    rows = (await http.get("/api/v1/floor", headers=h)).json()
    orders = {
        row["active_order"]["id"]: row["active_order"]
        for row in rows
        if row["active_order"] is not None
    }

    # Ninguna comanda perdió líneas ni se le mezclaron las de otra.
    assert set(orders) == set(expected)
    for order_id, product_order in expected.items():
        assert [item["product_id"] for item in orders[order_id]["items"]] == product_order


async def test_kds_batch_keeps_each_order_separate(client):
    http, fake_email = client
    tokens = await _onboard_verify_login(
        http, fake_email, slug="lotekds", email="owner@lotekds.com"
    )
    h = _auth(tokens)

    product_id = (
        await http.post(
            "/api/v1/products",
            json={"name": "Milanesa", "price_amount": 1000, "category": None},
            headers=h,
        )
    ).json()["product_id"]

    order_ids = []
    for number in (1, 2):
        table_id = (
            await http.post("/api/v1/tables", json={"number": number}, headers=h)
        ).json()["table_id"]
        order_id = (
            await http.post("/api/v1/orders", json={"table_id": table_id}, headers=h)
        ).json()["order_id"]
        await http.post(
            f"/api/v1/orders/{order_id}/items",
            json={"product_id": product_id, "quantity": 2},
            headers=h,
        )
        await http.post(f"/api/v1/orders/{order_id}/send", headers=h)
        order_ids.append(order_id)

    response = await http.get("/api/v1/kds/orders", headers=h)
    assert response.status_code == 200, response.text
    kds = {order["id"]: order for order in response.json()}

    assert set(kds) == set(order_ids)
    for order_id in order_ids:
        # Cada comanda conserva su propia línea (no se duplicó ni se perdió).
        assert len(kds[order_id]["items"]) == 1
        assert kds[order_id]["items"][0]["quantity"] == 2


async def test_floor_with_no_active_orders_does_not_break(client):
    # El batch arma un IN (...) con los ids: con la lista vacía no debe generar
    # SQL inválido, solo devolver nada.
    http, fake_email = client
    tokens = await _onboard_verify_login(
        http, fake_email, slug="vacio", email="owner@vacio.com"
    )
    h = _auth(tokens)
    await http.post("/api/v1/tables", json={"number": 1}, headers=h)

    rows = (await http.get("/api/v1/floor", headers=h)).json()

    assert [row["active_order"] for row in rows] == [None]
