# Plan: Fundaciones MP Orders-QR (backend) — Fase 1 cobro QR interoperable

## Summary
Backend para cobrar una comanda con un **QR dinámico de Mercado Pago** generado por la app: nuevo adapter Orders-QR detrás del `PaymentGateway` port (crea/consulta/cancela una orden dinámica y devuelve el string del QR), provisioning de **store+POS** por tenant con su token OAuth, mapeo del **webhook** de la orden QR al `ConfirmGatewayPayment` existente, y un setting **`qr_payment_mode`** por tenant (`external` | `mp_dynamic`, default `external`). **Sin comisión** (el `integrator_id` es Fase 4). Reusa el motor de pago, el resolver de credenciales por tenant y el webhook ya construidos.

## User Story
Como **mozo/cajero** de un local con Mercado Pago conectado y modo `mp_dynamic`, quiero **generar un QR de MP por el monto a cobrar y que su pago se confirme solo**, para **cobrar sin posnet y sin conciliar a mano**.

## Problem → Solution
Hoy `PaymentMethod.QR` en el cobro es un registro manual (o, con `payment_gateway=mercadopago`, un link de Checkout Pro) → **no genera un QR dinámico interoperable ni concilia solo**. Solución: un adapter que usa la **Orders API** de MP (`POST /v1/orders`, `config.qr.mode: dynamic`) para devolver un QR que cualquier billetera paga (interoperable por Transferencias 3.0), y el webhook existente lo confirma vía `external_reference`.

## Metadata
- **Complexity**: Large
- **Source PRD**: `.claude/PRPs/prds/cobro-qr-interoperable-mp.prd.md`
- **PRD Phase**: Fase 1 — Fundaciones MP Orders-QR (backend)
- **Estimated Files**: ~16 (7 CREATE, 9 UPDATE) + 1 migración

---

## UX Design
**N/A — cambio interno de backend.** La UX (render del QR + espera de confirmación) es la Fase 2 (mobile). Esta fase se valida por API/tests. Único efecto de cara al usuario: aparece el endpoint de Ajustes para elegir el modo QR (se consume en Fase 3).

---

## Mandatory Reading

| Priority | File | Lines | Why |
|---|---|---|---|
| P0 | `backend/app/domain/payment/ports.py` | 10-107 | `PaymentGateway`, `PaymentNotificationGateway`, `PaymentCredentialsResolver`, `OAuthTokens` — los ports a implementar/reusar |
| P0 | `backend/app/infrastructure/payments/mercadopago_gateway.py` | 1-184 | Patrón EXACTO a espejar: cliente httpx, `external_reference`, `charge`, `verify_signature`, `fetch_status`, `_STATUS_MAP` |
| P0 | `backend/app/application/payment/use_cases.py` | 124-222 (RegisterPayment), 311-410 (ConfirmGatewayPayment) | Dónde se llama `gateway.charge` y cómo el webhook confirma vía `external_reference` |
| P0 | `backend/app/domain/payment/entities.py` | 11-59 | `Payment` — campos transient `qr_data`/`checkout_url`/`external_ref` (NO persistidos) donde va el QR |
| P1 | `backend/app/presentation/api/v1/webhooks.py` | 1-66 | El webhook público `/webhooks/mercadopago`; hay que agregar el guard `type=payment` |
| P1 | `backend/app/infrastructure/payments/credentials_resolver.py` | 27-75 | `for_tenant` (token vigente) + `tenant_for_account` (routing webhook) |
| P1 | `backend/app/domain/payment/credentials.py` | 17-40 | `PaymentCredential` — sumar `store_id`/`pos_id` |
| P1 | `backend/app/infrastructure/persistence/models.py` | 55-75 (tenant flags), 495-523 (PaymentCredentialORM) | Patrón de columna con `server_default` + ORM de credenciales |
| P1 | `backend/app/application/payment/self_pay.py` | 1-40 | Patrón get/update de settings por tenant a espejar para `qr_payment_mode` |
| P1 | `backend/app/infrastructure/persistence/self_pay_settings_repo.py` | 1-50 | Repo que lee/escribe columnas del tenant directo (a espejar) |
| P1 | `backend/app/application/payment/connect_mercadopago.py` | 83-127 | `CompleteMercadoPagoConnection` — el `external_account_id` (user_id vendedor) para `POST /users/{user_id}/stores` |
| P1 | `backend/app/container.py` | 1069-1160 | Wiring de gateway/resolver/confirm/register + el `providers.Selector` |
| P2 | `backend/app/config.py` | 85-98, 230-234 | Settings MP + fail-fast (no hacen falta secretos nuevos) |
| P2 | `backend/app/presentation/api/v1/self_pay.py` | 24-40 | Patrón de router de settings (a espejar para `qr_payment_mode`) |
| P2 | `backend/tests/integration/test_e2e_webhook.py` / `test_e2e_payments.py` | all | Patrón de test con `httpx.MockTransport` y `container.override` |

## External Documentation

| Topic | Source | Key Takeaway |
|---|---|---|
| Orders API QR dinámico | MP `/v1/orders` (`config.qr.mode: dynamic`) | Crea la orden y devuelve el **string del QR**; `GET /v1/orders/{id}`, `POST /v1/orders/{id}/cancel`. **Confirmar la ruta exacta del QR en la respuesta contra sandbox.** |
| Store + POS | `POST /users/{user_id}/stores` + `POST /v2/pos` | Requisito de MP para el QR dinámico. `user_id` = `external_account_id` del vendedor. Idempotente por `external_id`. |
| Routing del webhook | `external_reference` = `"<tenant_id>:<payment_id>"` | MP propaga el `external_reference` de la orden al **pago** → el webhook `type=payment` existente enrutará sin cambios. |
| Interoperabilidad | BCRA Transferencias 3.0 | El QR dinámico es interoperable por norma; NO requiere programa especial ni `marketplace_fee`. La comisión es Fase 4 (`integration_data.integrator_id`). |

---

## Patterns to Mirror

### GATEWAY_CHARGE (crear el charge online y devolver el artefacto transient)
// SOURCE: backend/app/infrastructure/payments/mercadopago_gateway.py:86-143
```python
async def charge(self, *, payment: Payment) -> Payment:
    if payment.direction is PaymentDirection.OUTFLOW or payment.method not in _ONLINE_METHODS:
        payment.confirm()
        return payment
    creds = await self._resolver.for_tenant(payment.tenant_id)
    body: dict[str, object] = {
        "items": items,
        "external_reference": f"{payment.tenant_id}:{payment.id}",
    }
    async with self._client(creds.access_token) as client:
        resp = await client.post("/checkout/preferences", json=body)
        resp.raise_for_status()
        data = resp.json()
    payment.external_ref = str(data.get("id"))
    payment.qr_data = link           # ← el nuevo adapter pone acá el string del QR dinámico
    return payment
```

### CLIENT_HTTPX (cliente inyectable para tests)
// SOURCE: backend/app/infrastructure/payments/mercadopago_gateway.py:78-84
```python
def _client(self, access_token: str) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=_API_BASE, transport=self._transport,   # transport = httpx.MockTransport en tests
        headers={"Authorization": f"Bearer {access_token}"}, timeout=10.0)
```

### WEBHOOK_CONFIRM (routing por external_reference — se reusa TAL CUAL)
// SOURCE: backend/app/application/payment/use_cases.py:376-392
```python
ref = status.external_reference
if not ref or ":" not in ref:
    return  # not one of ours
tenant_id, payment_id = ref.split(":", 1)
payment = await self._payments.get_by_id(tenant_id, payment_id)
if payment is None or payment.status is PaymentStatus.CONFIRMED:
    return  # idempotent no-op
if status.status is PaymentStatus.CONFIRMED:
    payment.confirm()
    await self._payments.save(payment)
```

### SETTINGS_VALUE + REPO (por-tenant, a espejar para qr_payment_mode)
// SOURCE: backend/app/domain/payment/self_pay_settings.py:7-28
```python
@dataclass(frozen=True)
class SelfPaySettings:
    enabled: bool = False
    tips_enabled: bool = True

class SelfPaySettingsRepository(ABC):
    @abstractmethod
    async def get(self, tenant_id: str) -> SelfPaySettings: ...
    @abstractmethod
    async def update(self, tenant_id: str, settings: SelfPaySettings) -> None: ...
```

### SETTINGS_REPO_IMPL (columna en tenants, lectura/escritura directa)
// SOURCE: backend/app/infrastructure/persistence/self_pay_settings_repo.py:22-49
```python
row = (await db.execute(select(TenantORM.self_pay_enabled, TenantORM.self_pay_tips_enabled)
        .where(TenantORM.id == tenant_id))).one_or_none()
...
await db.execute(update(TenantORM).where(TenantORM.id == tenant_id)
                 .values(self_pay_enabled=settings.enabled, ...))
```

### TENANT_COLUMN (columna nueva con server_default → paridad)
// SOURCE: backend/app/infrastructure/persistence/models.py:66-70
```python
self_order_prepay_required: Mapped[bool] = mapped_column(
    Boolean, nullable=False, server_default="false")
```

### CONTAINER_SELECTOR + FACTORY (wiring por flag / inyección por constructor)
// SOURCE: backend/app/container.py:1106-1123
```python
payment_gateway = providers.Selector(
    config.provided.payment_gateway,
    manual=providers.Singleton(ManualPaymentGateway),
    mercadopago=mercadopago_gateway)
register_payment = providers.Factory(
    RegisterPayment, payments=payment_repository, orders=order_repository,
    gateway=payment_gateway, tenant_context=tenant_context, ...)
```

### CREDENTIAL_UPSERT (persistir store_id/pos_id junto a las credenciales)
// SOURCE: backend/app/infrastructure/persistence/credentials_repo.py:38-40
```python
async def upsert(self, credential: PaymentCredential) -> None:
    async with self._session_factory() as session:
        await session.merge(payment_credential_to_orm(credential))
```

---

## Files to Change

| File | Action | Justification |
|---|---|---|
| `backend/app/domain/payment/qr_settings.py` | CREATE | `QrPaymentMode` (enum EXTERNAL/MP_DYNAMIC) + `QrPaymentSettings` value + `QrPaymentSettingsRepository` port |
| `backend/app/domain/payment/ports.py` | UPDATE | Nuevo port `MpQrProvisioner` (`ensure_pos`) + dataclass `QrPos(store_id, pos_id)` |
| `backend/app/domain/payment/credentials.py` | UPDATE | `PaymentCredential`: sumar `store_id: str | None`, `pos_id: str | None` |
| `backend/app/infrastructure/payments/mercadopago_qr_gateway.py` | CREATE | Adapter Orders-QR: `charge` para `PaymentMethod.QR` → crea orden dinámica, devuelve `qr_data` |
| `backend/app/infrastructure/payments/mercadopago_qr_provisioner.py` | CREATE | Adapter store+POS (`POST /users/{uid}/stores`, `POST /v2/pos`), idempotente, persiste store/pos |
| `backend/app/infrastructure/persistence/qr_payment_settings_repo.py` | CREATE | Repo `qr_payment_mode` (columna en `tenants`), espeja `self_pay_settings_repo` |
| `backend/app/application/payment/qr_settings.py` | CREATE | `GetQrPaymentSettings` + `UpdateQrPaymentSettings` (espeja `self_pay.py`) |
| `backend/app/presentation/api/v1/payments.py` (o `self_pay.py`) | UPDATE | Endpoints `GET/PUT` de `qr_payment_mode` (Ajustes) |
| `backend/app/presentation/schemas/` | UPDATE | Schemas request/response del setting |
| `backend/app/application/payment/use_cases.py` | UPDATE | `RegisterPayment`: rutear `method==QR` + modo `mp_dynamic` al `qr_gateway` |
| `backend/app/presentation/api/v1/webhooks.py` | UPDATE | Guard `type=payment` (ignorar `merchant_order`/`topic=order`) |
| `backend/app/infrastructure/persistence/models.py` | UPDATE | `PaymentCredentialORM`: `store_id`/`pos_id`; `TenantORM`: `qr_payment_mode` |
| `backend/app/infrastructure/persistence/mappers.py` | UPDATE | Mapear `store_id`/`pos_id` en `payment_credential_to_domain/orm` |
| `backend/alembic/versions/0054_qr_payment.py` | CREATE | `store_id`/`pos_id` en `payment_credentials` + `qr_payment_mode` en `tenants` (server_default `'EXTERNAL'`) |
| `backend/app/container.py` | UPDATE | Wiring: `mp_qr_provisioner`, `mercadopago_qr_gateway`, `qr_payment_settings_repository`, get/update use cases, inyectar en `register_payment` |
| `backend/app/config.py` | UPDATE (opcional) | Solo si se agrega un flag maestro; NO hay secretos nuevos |
| `backend/tests/integration/test_e2e_qr_payment.py` | CREATE | Cobro QR dinámico + webhook end-to-end con `MockTransport` |
| `backend/tests/**` (unit) | CREATE | Unit del adapter QR, del provisioner, del ruteo en `RegisterPayment`, del repo de settings |

## NOT Building
- **Comisión / `integration_data.integrator_id`** — Fase 4 (alta de integrador con MP).
- **`marketplace_fee`** — no existe en el flujo QR.
- **UI mobile / render del QR / espera** — Fase 2.
- **Selector de modo en Ajustes (UI)** — Fase 3 (acá solo el endpoint).
- **Flujo aceptador de crédito interoperable / homologación** — Fase 5.
- **Carta QR web del comensal** — sigue con Checkout Pro; fuera de alcance.

---

## Step-by-Step Tasks

### Task 1: `qr_payment_mode` — dominio + repo + migración
- **ACTION**: Crear el value/enum + port, la columna en `tenants` y el repo.
- **IMPLEMENT**: `backend/app/domain/payment/qr_settings.py`: `class QrPaymentMode(StrEnum): EXTERNAL="EXTERNAL"; MP_DYNAMIC="MP_DYNAMIC"`; `@dataclass(frozen=True) class QrPaymentSettings: mode: QrPaymentMode = QrPaymentMode.EXTERNAL`; `class QrPaymentSettingsRepository(ABC)` con `get`/`update`. En `models.py::TenantORM` sumar `qr_payment_mode: Mapped[str] = mapped_column(String(16), nullable=False, server_default="EXTERNAL")`. Repo `qr_payment_settings_repo.py` espejando `self_pay_settings_repo.py`.
- **MIRROR**: SETTINGS_VALUE + REPO, SETTINGS_REPO_IMPL, TENANT_COLUMN.
- **IMPORTS**: `from enum import StrEnum`; `from sqlalchemy import select, update`; `from app.infrastructure.persistence.models import TenantORM`.
- **GOTCHA**: `server_default="EXTERNAL"` es obligatorio → los tenants existentes quedan en modo manual (paridad). El dominio es Python puro: NO importar SQLAlchemy en `qr_settings.py`.
- **VALIDATE**: `poetry run pytest tests/ -k qr_settings`.

### Task 2: Migración 0054
- **ACTION**: `alembic revision` manual `0054_qr_payment` con `down_revision = "0053"`.
- **IMPLEMENT**: `op.add_column("payment_credentials", sa.Column("store_id", sa.String(64), nullable=True))` + `pos_id`; `op.add_column("tenants", sa.Column("qr_payment_mode", sa.String(16), nullable=False, server_default="EXTERNAL"))`. `downgrade` dropea las 3.
- **MIRROR**: última migración `0053_device_tokens.py` (estructura + estilo).
- **GOTCHA**: head actual = **0053**. NO correr `alembic upgrade` a mano en prod (Railway lo corre en `preDeployCommand`). Sí correrlo local contra la DB de dev para validar.
- **VALIDATE**: `poetry run alembic upgrade head` (local) → sin error; `poetry run alembic heads` = un solo head.

### Task 3: `PaymentCredential` gana store_id/pos_id
- **ACTION**: Sumar `store_id`/`pos_id` al dataclass, al ORM y a los mappers.
- **IMPLEMENT**: `credentials.py`: `store_id: str | None = None`, `pos_id: str | None = None`. `models.py::PaymentCredentialORM`: dos `mapped_column(String(64), nullable=True)`. `mappers.py`: mapear en `payment_credential_to_domain`/`_to_orm`.
- **MIRROR**: CREDENTIAL_UPSERT + el ORM existente (models.py:495-523).
- **GOTCHA**: mantener el orden/estilo de campos; no romper el `merge` del upsert.
- **VALIDATE**: `poetry run pytest tests/ -k credential`.

### Task 4: Port `MpQrProvisioner` + adapter
- **ACTION**: Definir el port y el adapter que asegura store+POS del tenant.
- **IMPLEMENT**: en `ports.py`: `@dataclass(frozen=True) class QrPos: store_id: str; pos_id: str` + `class MpQrProvisioner(ABC): async def ensure_pos(self, *, user_id: str, access_token: str, external_id: str) -> QrPos`. Adapter `mercadopago_qr_provisioner.py`: si no existe, `POST /users/{user_id}/stores` (name/external_id) → store_id; `POST /v2/pos` (store_id, external_id, `config.qr.operating_mode="pdv"`) → pos_id; idempotente (consultar antes o manejar el 400 de "ya existe" por `external_id`).
- **MIRROR**: CLIENT_HTTPX + GATEWAY_CHARGE (mismo estilo httpx/`_API_BASE`/`raise_for_status`).
- **IMPORTS**: `import httpx`; `from app.domain.payment.ports import MpQrProvisioner, QrPos`.
- **GOTCHA**: `external_id` estable por tenant (ej. `f"wellnod-{tenant_id}"`) para idempotencia. Confirmar contra sandbox la respuesta de `stores`/`pos`. Credenciales NUNCA se loguean.
- **VALIDATE**: unit con `MockTransport` (stores→id, pos→id; segunda llamada no duplica).

### Task 5: Adapter `MercadoPagoQrGateway`
- **ACTION**: Nuevo `PaymentGateway` que para `PaymentMethod.QR` crea la orden dinámica.
- **IMPLEMENT**: `mercadopago_qr_gateway.py`: `charge` — si `method != QR` → `payment.confirm(); return`. Si `QR`: `creds = resolver.for_tenant(tenant)`; asegurar store/pos (leer de `PaymentCredential` o `provisioner.ensure_pos`); `POST /v1/orders` con `type="qr"`, `config.qr.mode="dynamic"`, `external_reference=f"{tenant}:{payment.id}"`, `total_amount` (mayor units, string) + items (sale + propina como en el gateway actual). De la respuesta: `payment.external_ref = order_id`; `payment.qr_data = <qr string>`; status PENDING.
- **MIRROR**: GATEWAY_CHARGE + CLIENT_HTTPX.
- **IMPORTS**: `from app.domain.payment.ports import PaymentGateway, PaymentCredentialsResolver, MpQrProvisioner`; `from app.domain.payment.value_objects import PaymentMethod, PaymentDirection`.
- **GOTCHA**: `external_reference` con el MISMO formato `"<tenant>:<payment_id>"` (lo exige el webhook existente). El monto en MP Orders va en **unidad mayor** (dividir `amount` por `_MINOR_UNIT`). Confirmar en sandbox el campo exacto del QR en la respuesta (`qr_data`/`type_response.qr_data`).
- **VALIDATE**: unit con `MockTransport` → `payment.qr_data` no vacío, `external_ref`=order id, status PENDING.

### Task 6: Rutear QR-dinámico en `RegisterPayment`
- **ACTION**: Que `RegisterPayment` use el `qr_gateway` cuando corresponde.
- **IMPLEMENT**: sumar params opcionales `qr_gateway: PaymentGateway | None = None` y `qr_mode: QrPaymentSettingsRepository | None = None`. Antes de `self._gateway.charge(...)`: si `PaymentMethod(method) is PaymentMethod.QR and qr_mode and (await qr_mode.get(tenant_id)).mode is QrPaymentMode.MP_DYNAMIC and self._qr_gateway`: `payment = await self._qr_gateway.charge(payment=payment)`; else el `self._gateway.charge` actual. Todo lo demás (idempotencia, settle) igual.
- **MIRROR**: RegisterPayment (use_cases.py:195-212).
- **GOTCHA**: Modo `external` → NO tocar MP: cae al `gateway` actual (con `payment_gateway=manual` confirma al toque = comportamiento de hoy). Mantener params opcionales para no romper los tests/DI existentes.
- **VALIDATE**: unit — mode EXTERNAL usa el gateway base; mode MP_DYNAMIC usa el qr_gateway (con fakes).

### Task 7: Webhook — guard `type=payment`
- **ACTION**: Ignorar notificaciones que no sean de pago (la Orders API también manda `merchant_order`/`topic=order`).
- **IMPLEMENT**: en `webhooks.py::mercadopago_webhook` leer `type: Annotated[str | None, Query()] = None` (y `topic`); si `type` no es `"payment"` (y `topic` no es de pago) → `return {"status": "ignored"}` antes de `fetch_status`.
- **MIRROR**: webhooks.py:35-65.
- **GOTCHA**: sin este guard, un `merchant_order` haría `GET /v1/payments/{order_id}` → 404. `ConfirmGatewayPayment` NO cambia: el pago aprobado propaga el `external_reference` de la orden.
- **VALIDATE**: `test_e2e_webhook` — un `type=merchant_order` se ignora; un `type=payment` con el `external_reference` correcto confirma el pago.

### Task 8: Use cases + endpoint de `qr_payment_mode` (Ajustes)
- **ACTION**: `GetQrPaymentSettings`/`UpdateQrPaymentSettings` + `GET/PUT` en el router.
- **IMPLEMENT**: `application/payment/qr_settings.py` espejando `self_pay.py`. Endpoint (en `payments.py` o `self_pay.py`) `GET /payments/qr-settings` + `PUT /payments/qr-settings` (roles OWNER/MANAGER). En `UpdateQrPaymentSettings.execute`: si `mode==MP_DYNAMIC`, validar que el tenant tenga MP conectado (opcional en Fase 1; gate fuerte en Fase 3) → si no, `PaymentGatewayNotConnected`/`code` en español.
- **MIRROR**: self_pay.py (use cases) + self_pay.py router (presentation).
- **GOTCHA**: mensaje de error con `code` en inglés + `message` en español (convención). Roles vía `require_roles(Role.OWNER, Role.MANAGER)`.
- **VALIDATE**: `test_e2e` — PUT cambia el modo; GET lo refleja; sin rol → 403.

### Task 9: Wiring en `container.py`
- **ACTION**: Cablear provisioner, qr gateway, repo de settings y use cases; inyectar en `register_payment`.
- **IMPLEMENT**: `mp_qr_provisioner = providers.Singleton(MercadoPagoQrProvisioner, credentials_resolver=..., credentials=payment_credential_repository)`; `mercadopago_qr_gateway = providers.Singleton(MercadoPagoQrGateway, credentials_resolver=payment_credentials_resolver, provisioner=mp_qr_provisioner)`; `qr_payment_settings_repository = providers.Factory(SqlAlchemyQrPaymentSettingsRepository, session_factory=db.provided.session)`; get/update use cases; en `register_payment` sumar `qr_gateway=mercadopago_qr_gateway, qr_mode=qr_payment_settings_repository`.
- **MIRROR**: CONTAINER_SELECTOR + FACTORY (container.py:1071-1123).
- **GOTCHA**: `register_public_payment` (Carta QR comensal) NO recibe el qr_gateway (ese cobro es Checkout Pro online, no el QR presencial del cajero). Agregar los imports arriba en `container.py`.
- **VALIDATE**: `poetry run python -c "from app.container import Container; Container()"` sin error de wiring; suite completa verde.

### Task 10: Tests de integración + unit
- **ACTION**: Cubrir el flujo end-to-end y las piezas.
- **IMPLEMENT**: `test_e2e_qr_payment.py`: tenant con `qr_payment_mode=mp_dynamic` + credencial MP (fake) → `POST /payments` method QR devuelve `qr_data`; simular webhook `type=payment` con el `external_reference` → el pago pasa a CONFIRMED y la orden concilia. Unit: provisioner (idempotente), qr gateway (arma el body correcto), ruteo en RegisterPayment, repo de settings.
- **MIRROR**: `tests/integration/test_e2e_webhook.py` + `test_e2e_payments.py` (`httpx.MockTransport`, `container.*.override(...)`).
- **GOTCHA**: usar `MockTransport` para MP (nunca red real). Cobertura 80%+ en dominio/casos de uso.
- **VALIDATE**: `poetry run pytest tests/ -k "qr or webhook or payment"`.

---

## Testing Strategy

### Unit Tests
| Test | Input | Expected Output | Edge Case? |
|---|---|---|---|
| QrGateway arma el body | payment QR $3110 | `POST /v1/orders` con `config.qr.mode=dynamic`, `external_reference="t:p"`, total en mayor units | No |
| QrGateway devuelve QR | respuesta MP con qr string | `payment.qr_data` set, `external_ref`=order id, status PENDING | No |
| QrGateway no-QR | method CASH | `payment.confirm()` sin llamar a MP | Sí |
| Provisioner idempotente | 2 llamadas mismo tenant | una sola creación store/pos | Sí |
| RegisterPayment ruteo | mode EXTERNAL vs MP_DYNAMIC | usa gateway base vs qr_gateway | Sí |
| Settings repo | tenant sin fila | default `EXTERNAL` | Sí |
| Webhook guard | `type=merchant_order` | ignorado, sin fetch_status | Sí |

### Edge Cases Checklist
- [ ] Tenant sin MP conectado + mode MP_DYNAMIC → `PaymentGatewayNotConnected` (no crashea el cobro)
- [ ] `external_reference` ajeno / sin `:` en el webhook → ignorado
- [ ] Webhook repetido (pago ya CONFIRMED) → no-op idempotente
- [ ] Monto con decimales → unidad mayor correcta
- [ ] Permisos: PUT qr-settings sin OWNER/MANAGER → 403

---

## Validation Commands

### Static Analysis
```bash
cd backend && poetry run ruff check app tests
```
EXPECT: Zero errors. **NO** correr formatters/ruff que toquen `app/presentation/api/v1/me.py` ni `auth.py` (excluir explícitamente si hace falta).

### Unit + Integration
```bash
cd backend && poetry run pytest tests/ -k "qr or webhook or payment or credential or settings"
```
EXPECT: All pass.

### Full Suite
```bash
cd backend && poetry run pytest
```
EXPECT: No regressions.

### Database / Migration
```bash
cd backend && poetry run alembic upgrade head && poetry run alembic heads
```
EXPECT: aplica 0054 sin error; un solo head.

### Manual Validation (contra sandbox MP)
- [ ] Con credencial de prueba, `POST /payments` (QR, mp_dynamic) devuelve un `qr_data` escaneable
- [ ] Pago de prueba dispara el webhook → el pago queda CONFIRMED y la orden PAID

---

## Acceptance Criteria
- [ ] `POST /payments` method QR con tenant `mp_dynamic` devuelve `qr_data` (string del QR) y status PENDING
- [ ] El webhook `type=payment` confirma el pago vía `external_reference` y concilia la orden
- [ ] Tenant `external` (default) → QR sigue siendo registro manual (paridad, cero cambios)
- [ ] `GET/PUT /payments/qr-settings` leen/cambian el modo (OWNER/MANAGER)
- [ ] store/pos se provisionan idempotentemente y quedan en `payment_credentials`
- [ ] Migración 0054 aplicada; sin comisión (Fase 4)

## Completion Checklist
- [ ] Sigue los patrones descubiertos (gateway/httpx/settings/ORM)
- [ ] `domain` sin imports de frameworks
- [ ] Errores con `code` (EN) + `message` (ES)
- [ ] Tests espejando `test_e2e_*` con `MockTransport`
- [ ] Multi-tenant: `external_reference` y queries por `tenant_id`
- [ ] Sin secretos nuevos; credenciales nunca logueadas
- [ ] `me.py`/`auth.py`/`.mcp.json` intactos

## Risks
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| La forma real de la respuesta Orders-QR (dónde viene el string del QR) difiere | Media | Alto | Validar contra sandbox antes de fijar el parseo; aislar en el adapter |
| MP manda `merchant_order` y rompe `fetch_status` | Media | Medio | Guard `type=payment` (Task 7) |
| `external_reference` no se propaga de la orden al pago | Baja-Media | Alto | Confirmar en sandbox; si no propaga, resolver el pago vía la orden en `fetch_status` |
| `payment_gateway` global (`manual` en prod) interfiere | Media | Medio | El ruteo QR-dinámico va por `qr_gateway` inyectado, independiente del flag global |
| Provisioning duplica store/POS | Baja | Bajo | `external_id` estable por tenant + idempotencia |

## Notes
- **Comisión (Fase 4):** cuando MP asigne el `integrator_id`, se agrega `integration_data.integrator_id` al body de `POST /v1/orders` en `MercadoPagoQrGateway` — un solo punto de cambio, sin tocar el resto.
- **OAuth ya existe** (`integrations/mercadopago/connect|callback`, `payment_credentials`, resolver con refresh) → esta fase NO construye conexión, solo la consume + suma store/pos.
- **Provisioning: lazy vs al conectar.** Recomendado lazy (en el gateway, primera vez que cobra por QR) para cubrir tenants ya conectados sin tocar el connect flow; alternativa: extender `CompleteMercadoPagoConnection`.

---

*Generated: 2026-09-04*
*Status: DRAFT - ready for /prp-implement*
