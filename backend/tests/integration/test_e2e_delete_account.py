"""Borrar la propia cuenta desde la app — requisito 5.1.1(v) de la App Store.

Apple exige que quien puede crear una cuenta desde la app pueda borrarla desde la
app. Acá eso tiene un filo: la cuenta de un dueño ES el local. Estos tests fijan
que los dos casos se distingan, porque confundirlos es o dejar un negocio sin
nadie que pueda entrar, o borrarle el historial a alguien que solo quería irse.
"""

from __future__ import annotations

from tests.integration.test_e2e_auth import (
    PASSWORD,
    _login,
    _onboard_verify_login,
    _token_from_link,
)
from tests.integration.test_e2e_payments import _auth


async def _invite_waiter(http, fake_email, h, *, slug: str, email: str) -> dict:
    assert (
        await http.post(
            "/api/v1/users/invite", json={"email": email, "role": "WAITER"}, headers=h
        )
    ).status_code == 201
    token = _token_from_link(fake_email.last().link)
    assert (
        await http.post(
            "/api/v1/users/accept-invitation",
            json={"token": token, "password": "WaiterPass1!"},
        )
    ).status_code == 200
    return _auth(await _login(http, slug=slug, email=email, password="WaiterPass1!"))


async def test_the_scope_says_whether_the_business_goes_too(client):
    """La confirmación tiene que poder decir la verdad ANTES de borrar."""
    http, fake_email = client
    h = _auth(
        await _onboard_verify_login(http, fake_email, slug="alcance", email="o@alcance.com")
    )

    owner = (await http.get("/api/v1/me/deletion-scope", headers=h)).json()
    assert owner["deletes_business"] is True, "dueño único: se va el local entero"
    assert owner["tenant_name"]

    wh = await _invite_waiter(http, fake_email, h, slug="alcance", email="w@alcance.com")
    waiter = (await http.get("/api/v1/me/deletion-scope", headers=wh)).json()
    assert waiter["deletes_business"] is False, "un mozo solo se lleva su acceso"


async def test_a_waiter_leaving_does_not_touch_the_business(client):
    http, fake_email = client
    h = _auth(
        await _onboard_verify_login(http, fake_email, slug="mozo", email="o@mozo.com")
    )
    wh = await _invite_waiter(http, fake_email, h, slug="mozo", email="w@mozo.com")

    gone = await http.request(
        "DELETE", "/api/v1/me", json={"password": "WaiterPass1!"}, headers=wh
    )
    assert gone.status_code == 200, gone.text
    assert gone.json()["deletes_business"] is False

    # El local sigue en pie y el dueño sigue entrando.
    assert (await http.get("/api/v1/me", headers=h)).status_code == 200
    # El mozo ya no puede volver a entrar.
    dead = await http.post(
        "/api/v1/auth/login",
        data={"username": "w@mozo.com", "password": "WaiterPass1!", "client_id": "mozo"},
    )
    assert dead.status_code == 401


async def test_the_password_is_required_even_with_a_valid_token(client):
    """Un teléfono desbloqueado sobre la barra no da de baja el local de un toque."""
    http, fake_email = client
    h = _auth(
        await _onboard_verify_login(http, fake_email, slug="clave", email="o@clave.com")
    )

    nope = await http.request(
        "DELETE", "/api/v1/me", json={"password": "NoEsLaMia1!"}, headers=h
    )
    assert nope.status_code in (401, 403), nope.text
    assert (await http.get("/api/v1/me", headers=h)).status_code == 200, "sigue viva"


async def test_the_last_owner_deletes_the_whole_business(client):
    """Borrar solo su usuario dejaría un local con datos y sin nadie que entre."""
    http, fake_email = client
    tokens = await _onboard_verify_login(
        http, fake_email, slug="local", email="o@local.com"
    )
    h = _auth(tokens)
    wh = await _invite_waiter(http, fake_email, h, slug="local", email="w@local.com")

    gone = await http.request(
        "DELETE", "/api/v1/me", json={"password": PASSWORD}, headers=h
    )
    assert gone.status_code == 200, gone.text
    assert gone.json()["deletes_business"] is True

    # Se fue el local: ni el dueño ni el resto del equipo pueden entrar.
    for email, pwd in (("o@local.com", PASSWORD), ("w@local.com", "WaiterPass1!")):
        dead = await http.post(
            "/api/v1/auth/login",
            data={"username": email, "password": pwd, "client_id": "local"},
        )
        assert dead.status_code == 401, f"{email} todavía entra"
    # El token del mozo sigue siendo criptográficamente válido —nadie lo revocó—
    # pero ya no hay usuario detrás. Da 404, no 401: el token se valida sin tocar
    # la base. No es un agujero (el filtro por tenant + RLS dejan todo vacío), pero
    # el cliente tiene que leer "mi perfil no existe" como sesión terminada y
    # desloguear, en vez de mostrar un error. Ver `_handleSessionGone` en el móvil.
    assert (await http.get("/api/v1/me", headers=wh)).status_code in (401, 403, 404)
