# Plan: Fase 3 — Cobro + Pagos

## Summary
Segundo módulo del motor operativo: **registrar y conciliar los cobros de una comanda** por todos los rieles (efectivo, MercadoPago/QR, posnet/tarjeta, transferencia), dejando la comanda en `PAID` cuando el total queda cubierto. Introduce el dominio `Payment` + el port `PaymentGateway` con **dos adapters reales: `ManualPaymentGateway`** (efectivo/transferencia) y **`MercadoPagoGateway`** (MercadoPago real, con webhook de confirmación), sobre la Clean Arch + multi-tenant + RLS + `Money` ya existentes. Es la primera fuente de dato de **plata cobrada / medios de pago** que después alimentará al asesor.

> **DECISIÓN DE ALCANCE (clave) — INTEGRACIÓN REAL:** este slice **SÍ integra MercadoPago real** (adapter `MercadoPagoGateway` + endpoint de webhook de confirmación), además del adapter manual (efectivo/transferencia) — ambos detrás del port `PaymentGateway`. **Siguen diferidos** los rieles **QR interoperable T3.0 (BCRA)** y **Payway/posnet** (integraciones separadas y más complejas; se enchufan después por el mismo port).
>
> **Prerrequisitos (los provee el usuario antes de implementar):**
> 1. **MCP de MercadoPago autenticado** (`/mcp` → mercadopago) — la API exacta (endpoints, payloads, firma de webhook) se consulta desde ahí durante la implementación; **no inventar la API**.
> 2. **Credenciales** MP (Access Token de **sandbox** primero) como **env vars** del backend (nunca al repo): `MP_ACCESS_TOKEN`, `MP_WEBHOOK_SECRET`.
> 3. **Webhook público**: túnel (ngrok/cloudflared) en dev o URL del backend en prod.
> 4. **Producto MP elegido** (link de pago / QR in-store / Point). Default propuesto: **link/preferencia de pago dinámico** (sin hardware).

## User Story
Como **cajero (CASHIER) / encargado (MANAGER) / dueño (OWNER)** quiero **registrar el cobro de una comanda eligiendo el medio de pago y el monto, y ver la comanda saldada**, para que **la plata cobrada quede registrada, conciliada con su comanda y discriminada por medio de pago**.

## Problem → Solution
Hoy la comanda termina en `SERVED` sin cobro (Fase 2). → El cajero **registra uno o más pagos** contra la comanda; cuando la suma de pagos confirmados cubre el total, la comanda pasa a **`PAID`**. Los pagos quedan tenant-scoped, con su medio y monto (`Money`), conciliados con la comanda. Los adapters de pasarelas reales se enchufan luego sin tocar el dominio.

## Estado de implementación (2026-06-20) — ✅ COMPLETA
Implementada por **3 tramos**, todos commiteados en `feat/fase-3-cobro-pagos`:
- **Tramo 1 (`df54a0a`)** — backend de pagos **manual** + dominio `Payment` (INFLOW/OUTFLOW) + `Order.PAID` + migración 0003 (RLS) + casos de uso + API `/orders/{id}/payments` y `/expenses`. 74 tests.
- **Tramo 2 (`05c8f48`)** — **`MercadoPagoGateway` real** (Checkout Pro link/QR vía httpx) + port `PaymentNotificationGateway` + **webhook firmado** `POST /api/v1/webhooks/mercadopago` (HMAC `x-signature`, idempotente, routing por `external_reference` sin token, concilia → `PAID`) + `providers.Selector` manual|mercadopago + config `MP_*`. 83 tests (adapter vía `httpx.MockTransport` + e2e webhook).
- **Tramo 3 (`bcf7c81`)** — frontend: `PaymentsApi` + hooks TanStack, bloque **Cobrar** en `order-page` (efectivo/tarjeta/transferencia confirman al toque; MP/QR muestran link + polling hasta `PAID`), página de **egresos**, ruteo/nav (CASHIER puede cobrar). tsc + eslint + 17 tests + build.

**Diferido (mismo port, después):** QR interoperable T3.0 (BCRA), Payway/posnet, money-out real de MP para egresos (hoy el egreso se registra/manual-confirma). Pendiente sólo **validación manual en vivo** con credenciales sandbox + túnel.

## Metadata
- **Complexity**: **XL** (dominio + persistencia + migración RLS + casos de uso + API + frontend de cobro; toca el agregado `Order` para sumar `PAID`). Partible en commits backend↔frontend (igual que Fase 2).
- **Source PRD**: `.claude/PRPs/prds/nucleo.prd.md`
- **PRD Phase**: Fase 3 — Cobro + Pagos
- **Estimated Files**: ~38 (≈26 backend, ≈12 frontend)

---

## UX Design

### Before
```
Comanda SERVED → no hay forma de cobrar; la plata cobrada no se registra.
```

### After
```
CAJERO (rol CASHIER/MANAGER/OWNER) — en /app/orders/:orderId
  Total: $3.800   |   Cobrado: $0
  [Registrar cobro] → medio (Efectivo/MercadoPago/QR/Posnet/Transferencia) + monto
  → Pago registrado (CONFIRMED), Cobrado: $3.800 ≥ Total → comanda PAID ✅
  Lista de pagos del pedido (medio + monto + estado)
```

### Interaction Changes
| Touchpoint | Before | After | Notes |
|---|---|---|---|
| Cobrar una comanda | — | registrar pago(s) por medio + monto | rol CASHIER/MANAGER/OWNER |
| Estado de la comanda | termina en SERVED | SERVED → **PAID** al cubrir el total | nueva transición en el agregado `Order` |
| Medios de pago | — | enum `PaymentMethod` (CASH/MERCADOPAGO/QR/CARD/TRANSFER) | base para conciliación del asesor |

---

## Mandatory Reading

Leer ANTES de implementar. **Fase 2 es el molde exacto** — imitar al pie de la letra. (Todo está en `main`.)

### Backend — molde (Fase 2)
| Prio | File | Why |
|---|---|---|
| P0 | `backend/app/domain/order/entities.py` | Agregado con máquina de estados → **agregar `mark_paid()`**; molde para `Payment` |
| P0 | `backend/app/domain/order/value_objects.py` | `OrderStatus` (StrEnum) → **agregar `PAID`**; molde para `PaymentMethod`/`PaymentStatus` |
| P0 | `backend/app/domain/shared/money.py` | `Money` (entero + ISO-4217) — el pago usa `Money` |
| P0 | `backend/app/domain/product/{entities,exceptions,repository}.py` | Molde simple entidad + port + excepciones para `Payment` |
| P0 | `backend/app/application/order/use_cases.py` | Use case: ctor inyecta ports, `async execute(*,...)`, `tenant_context.set()`, `str(uuid4())`, levanta DomainError → molde `RegisterPayment` |
| P0 | `backend/app/infrastructure/persistence/{models,mappers}.py` | ORM tenant-scoped (BigInteger para montos) + mappers (omiten created_at) → `PaymentORM` |
| P0 | `backend/app/infrastructure/persistence/order_repo.py` | Repo tenant-scoped → molde `payment_repo` (`list_by_order`) |
| P0 | `backend/alembic/versions/0002_orders_kds.py` | **Migración con `ENABLE/FORCE RLS` + policy `tenant_isolation`** → 0003 para `payments` |
| P0 | `backend/app/presentation/api/v1/orders.py` + `schemas/orders.py` | Router `@inject` + `require_roles`; `order_to_response` → molde pagos |
| P0 | `backend/app/container.py` + `main.py` + `presentation/errors.py` | Wiring repo+use cases, include_router, registrar excepciones |
| P1 | `backend/app/infrastructure/email/console_sender.py` + `app/domain/identity/ports.py` | Molde de **port + adapter** (email console) → `PaymentGateway` port + `ManualPaymentGateway` adapter |
| P1 | `backend/tests/integration/test_e2e_orders.py` + `tests/unit/test_order.py` | Molde de tests (e2e con DB + unit de dominio) |

### Frontend — molde (Fase 2)
| Prio | File | Why |
|---|---|---|
| P0 | `src/api/orders-api.ts` + `types-operations.ts` | Cliente inyectable + DTOs → `payments-api` |
| P0 | `src/services/services-context.ts` + `services-provider.tsx` | Agregar `paymentsApi` a `Services` |
| P0 | `src/hooks/use-orders.ts` | useMutation/useQuery + invalidate → `use-payments` |
| P0 | `src/features/orders/order-page.tsx` | Acá se agrega el bloque "Cobrar" + estado PAID |
| P0 | `src/lib/money.ts` | `formatMoney` |

---

## External Documentation

| Topic | Source | Key Takeaway |
|---|---|---|
| MercadoPago API (real) | **MCP `mercadopago`** (autenticado) | Consultar **desde el MCP** los endpoints/payloads exactos: crear preferencia/intención de pago, obtener `init_point`/QR, consultar estado del pago, y **formato + verificación de firma del webhook**. **No inventar la API** — leerla del MCP en tiempo de implementación. |
| Credenciales MP | env vars del backend | `MP_ACCESS_TOKEN` (sandbox primero), `MP_WEBHOOK_SECRET`. Nunca al repo ni a logs. |
| Webhook en dev | ngrok / cloudflared | URL pública para que MP notifique la confirmación del pago. |

> **Diferido (otra rebanada, mismo port):** QR interoperable Transferencias 3.0 (BCRA) y Payway/Fiserv (posnet).

---

## Patterns to Mirror

> Los snippets reales viven en los archivos de *Mandatory Reading*. Acá, las **formas nuevas**.

### PAYMENT_ENUMS
```python
# app/domain/payment/value_objects.py — MIRROR: OrderStatus (StrEnum)
class PaymentMethod(StrEnum):
    CASH = "CASH"; MERCADOPAGO = "MERCADOPAGO"; QR = "QR"; CARD = "CARD"; TRANSFER = "TRANSFER"

class PaymentStatus(StrEnum):
    PENDING = "PENDING"; CONFIRMED = "CONFIRMED"; FAILED = "FAILED"; REFUNDED = "REFUNDED"
```

### PAYMENT_ENTITY
```python
# app/domain/payment/entities.py — MIRROR: Product (entidad simple) + Money
@dataclass
class Payment:
    id: str; tenant_id: str; order_id: str
    amount: Money; method: PaymentMethod
    status: PaymentStatus = PaymentStatus.CONFIRMED  # manual = confirmado al registrar
    external_ref: str | None = None                  # id de la pasarela (futuro)
    created_at: datetime | None = None
    def confirm(self) -> None: self.status = PaymentStatus.CONFIRMED
    def fail(self) -> None: self.status = PaymentStatus.FAILED
```

### ORDER_MARK_PAID (extensión del agregado de Fase 2)
```python
# app/domain/order/entities.py — agregar; MIRROR: métodos existentes (_advance)
def mark_paid(self) -> None:
    if self.status in (OrderStatus.CANCELLED, OrderStatus.PAID):
        raise InvalidOrderTransition()
    self.status = OrderStatus.PAID
# y en value_objects.py: OrderStatus.PAID = "PAID"
```

### PAYMENT_GATEWAY_PORT (+ adapter manual)
```python
# app/domain/payment/ports.py — MIRROR: EmailSender port (domain/identity/ports.py)
class PaymentGateway(ABC):
    """Port para iniciar/confirmar cobros. El MVP usa el adapter manual; MP/QR/Payway luego."""
    @abstractmethod
    async def charge(self, *, payment: Payment) -> Payment: ...

# app/infrastructure/payments/manual_gateway.py — MIRROR: ConsoleEmailSender
class ManualPaymentGateway(PaymentGateway):
    """Registro manual: el cobro ya ocurrió fuera del sistema; se confirma de inmediato."""
    async def charge(self, *, payment: Payment) -> Payment:
        payment.confirm(); return payment
```

### REGISTER_PAYMENT_USE_CASE
```python
# app/application/payment/use_cases.py — MIRROR: AddOrderItem / order use_cases
class RegisterPayment:
    def __init__(self, payments, orders, gateway, tenant_context): ...
    async def execute(self, *, tenant_id, order_id, method, amount, currency) -> Payment:
        self._tenant_context.set(tenant_id)
        order = await self._orders.get_by_id(tenant_id, order_id)
        if order is None: raise OrderNotFound()
        if order.status in (OrderStatus.CANCELLED,): raise InvalidOrderTransition()
        payment = Payment(id=str(uuid4()), tenant_id=tenant_id, order_id=order_id,
                          amount=Money(amount, currency or order.currency), method=PaymentMethod(method))
        payment = await self._gateway.charge(payment=payment)
        await self._payments.add(payment)
        # conciliación: si la suma de pagos CONFIRMED cubre el total → PAID
        paid = sum(p.amount.amount for p in await self._payments.list_by_order(tenant_id, order_id)
                   if p.status is PaymentStatus.CONFIRMED)
        if paid >= order.total().amount and order.status is not OrderStatus.PAID:
            order.mark_paid(); await self._orders.save(order)
        return payment
```

### AGGREGATE/REPO/MIGRATION/ROUTER/TESTS
Idénticos a Fase 2: `payment_repo` (MIRROR `order_repo` sin la colección de hijos — Payment es plano), migración 0003 (MIRROR 0002, tabla `payments` con RLS policy), router `payments` (MIRROR `orders.py`, `require_roles(CASHIER, MANAGER, OWNER)`), DI (MIRROR container), tests (MIRROR `test_e2e_orders` + `test_order`).

---

## Files to Change

### Backend
| File | Action |
|---|---|
| `app/domain/payment/{__init__,entities,value_objects,exceptions,repository,ports}.py` | CREATE — Payment, enums, `PaymentNotFound/InvalidPaymentAmount`, `PaymentRepository`, `PaymentGateway` |
| `app/domain/order/value_objects.py` | UPDATE — `OrderStatus.PAID` |
| `app/domain/order/entities.py` | UPDATE — `mark_paid()` |
| `app/presentation/errors.py` | UPDATE — registrar `PaymentNotFound`(404), `InvalidPaymentAmount`(422) |
| `app/infrastructure/persistence/models.py` | UPDATE — `PaymentORM` (BigInteger `amount`, `currency`, `method`, `status`, `order_id` FK, `external_ref`) |
| `app/infrastructure/persistence/mappers.py` | UPDATE — `payment_to_domain/_to_orm` |
| `app/infrastructure/persistence/payment_repo.py` | CREATE — `get_by_id`, `list_by_order`, `add`, `save` |
| `app/infrastructure/payments/{__init__,manual_gateway}.py` | CREATE — `ManualPaymentGateway` |
| `alembic/versions/0003_payments.py` | CREATE — tabla `payments` + ENABLE/FORCE RLS + policy |
| `app/application/payment/{__init__,dtos,use_cases}.py` | CREATE — `RegisterPayment`, `ListOrderPayments` |
| `app/presentation/schemas/payments.py` | CREATE — `RegisterPaymentRequest`, `PaymentResponse` |
| `app/presentation/api/v1/payments.py` | CREATE — `POST /orders/{id}/payments`, `GET /orders/{id}/payments` |
| `app/container.py`, `app/main.py` | UPDATE — repo + gateway + use cases; include_router |
| `tests/unit/test_payment.py` | CREATE — Payment + mark_paid + conciliación |
| `tests/integration/test_e2e_payments.py` + `conftest.py` | CREATE/UPDATE (`_TABLES` += `payments`) |

### Frontend
| File | Action |
|---|---|
| `src/api/types-operations.ts` | UPDATE — `PaymentMethod`, `PaymentDTO`, agregar `PAID` a `OrderStatus` |
| `src/api/payments-api.ts` | CREATE — `register(orderId, method, amount)`, `listByOrder(orderId)` |
| `src/services/services-{context,provider}` | UPDATE — `paymentsApi` |
| `src/hooks/use-payments.ts` | CREATE — `useOrderPayments(orderId)`, `useRegisterPayment(orderId)` (invalida `["order",id]` + `["payments",id]`) |
| `src/lib/payment-labels.ts` | CREATE — labels ES de `PaymentMethod` |
| `src/features/orders/order-page.tsx` | UPDATE — bloque "Cobrar" (Select medio + monto) + lista de pagos + estado PAID |
| `src/test/*` | CREATE — test de `payments-api` + labels |

## NOT Building
- **Adapters reales de QR interoperable T3.0 y Payway/posnet** — diferidos (integraciones separadas; se enchufan después por el mismo port). **MercadoPago real SÍ entra** en este slice.
- **Conciliación batch** (posnet/transferencias por reporte) y **cola de excepciones de matching** — para la rebanada de QR/Payway. (El webhook de MP sí concilia el pago MP con su comanda.)
- **Reembolsos/anulaciones** (status `REFUNDED` existe en el enum pero sin flujo) — follow-up.
- **Propinas, split de cuenta, pago parcial multi-mesa** — fuera de alcance.
- **Facturación AFIP** — Fase 4.

---

## Step-by-Step Tasks

> Orden: dominio → persistencia → migración → use cases → API → tests → frontend. Validar (`ruff/mypy/pytest`, `tsc/lint/test/build`) por bloque. Mismos patrones que Fase 2.

### Task 1 — Dominio `Payment` + enums + port
- **ACTION**: crear el paquete `app/domain/payment/`.
- **IMPLEMENT**: `PaymentMethod`/`PaymentStatus` (StrEnum), `Payment` entity (con `confirm/fail`), `PaymentNotFound`/`InvalidPaymentAmount` (DomainError), `PaymentRepository` (ABC: get_by_id, list_by_order, add, save), `PaymentGateway` (ABC: `charge`).
- **MIRROR**: `PAYMENT_ENUMS`, `PAYMENT_ENTITY`, `PAYMENT_GATEWAY_PORT`; product domain.
- **VALIDATE**: `mypy app`.

### Task 2 — Order: estado `PAID`
- **ACTION**: extender el agregado.
- **IMPLEMENT**: `OrderStatus.PAID`; `Order.mark_paid()` (raise `InvalidOrderTransition` si CANCELLED/PAID).
- **MIRROR**: `ORDER_MARK_PAID`.
- **GOTCHA**: no romper los tests de Fase 2 (PAID es estado nuevo, no cambia transiciones existentes). Decisión: el KDS sigue mostrando solo SENT/PREPARING (PAID no afecta).
- **VALIDATE**: `pytest tests/unit/test_order.py` sigue verde + nuevo test de `mark_paid`.

### Task 3 — Registrar excepciones + ORM + mapper + repo
- **ACTION**: persistencia de `Payment`.
- **IMPLEMENT**: `errors.py` (+`PaymentNotFound` 404, `InvalidPaymentAmount` 422); `PaymentORM` (id, tenant_id FK, order_id FK, `amount BigInteger`, `currency String(3)`, `method String(20)`, `status String(20)`, `external_ref String|None`, created_at); mappers (`_to_orm` omite created_at); `SqlAlchemyPaymentRepository` (filtra tenant_id; `list_by_order` ordena por created_at).
- **MIRROR**: `models.py`/`mappers.py`/`order_repo.py` (Payment es plano, sin colección de hijos → más simple que Order).
- **VALIDATE**: `mypy app`.

### Task 4 — Migración 0003 (+ RLS)
- **ACTION**: `alembic/versions/0003_payments.py` (down_revision `0002_orders_kds`).
- **IMPLEMENT**: `Base.metadata.create_all(bind, tables=[PaymentORM.__table__])`; GRANT al rol; `ENABLE`+`FORCE RLS` + policy `tenant_isolation` en `payments`. Downgrade simétrico.
- **MIRROR**: `0002_orders_kds.py`.
- **VALIDATE**: `alembic upgrade head` → `downgrade -1` → `upgrade head`.

### Task 5 — Adapter `ManualPaymentGateway` + use cases
- **ACTION**: adapter + `application/payment/`.
- **IMPLEMENT**: `ManualPaymentGateway` (confirma de inmediato); `RegisterPayment` (crea Payment, `gateway.charge`, persiste, **concilia**: si suma de CONFIRMED ≥ total → `order.mark_paid()` + save); `ListOrderPayments`. DTO `PaymentResult`/`RegisterPaymentInput` si hace falta.
- **MIRROR**: `REGISTER_PAYMENT_USE_CASE`; `ManualPaymentGateway` ↔ `ConsoleEmailSender`.
- **GOTCHA**: monto del pago en la **moneda de la orden**; validar `amount > 0` (`InvalidPaymentAmount`). No permitir pago si order CANCELLED.
- **VALIDATE**: `pytest tests/unit/test_payment.py` (registra → concilia → PAID; pago parcial no marca PAID; monto inválido lanza).

### Task 6 — Schemas + router + wiring
- **ACTION**: API.
- **IMPLEMENT**: `RegisterPaymentRequest {method, amount}` (amount int minor units ≥ 1), `PaymentResponse {id, order_id, method, amount, currency, status}`; router `payments` con `POST /orders/{id}/payments` y `GET /orders/{id}/payments` (`require_roles(CASHIER, MANAGER, OWNER)`); container (repo + `ManualPaymentGateway` singleton + use cases); `main.py` include_router.
- **MIRROR**: `orders.py` router, `container.py`, `main.py`.
- **VALIDATE**: `ruff check . && mypy app`; app levanta.

### Task 7 — Tests backend (e2e + integración)
- **ACTION**: `tests/integration/test_e2e_payments.py`; `conftest._TABLES += "payments"`.
- **IMPLEMENT**: onboard→login→crear product/table/order→add item→**registrar pago < total** (order sigue no-PAID)→**registrar pago que completa** (order PAID)→`GET payments` lista ambos→aislamiento RLS (otro tenant no ve pagos).
- **MIRROR**: `test_e2e_orders.py`.
- **VALIDATE**: `pytest tests/unit tests/integration -q`.

### Task 8 — Frontend: cliente + DI + tipos + labels
- **ACTION**: capa de datos del cobro.
- **IMPLEMENT**: `types-operations.ts` (`PaymentMethod`, `PaymentDTO`, `OrderStatus` += `PAID`); `payments-api.ts` (`register`, `listByOrder`); agregar `paymentsApi` a `Services` + provider; `lib/payment-labels.ts` (Efectivo/MercadoPago/QR/Tarjeta/Transferencia).
- **MIRROR**: `orders-api.ts`, services.
- **VALIDATE**: `npm run typecheck`.

### Task 9 — Frontend: hooks + cobro en la comanda
- **ACTION**: hooks + UI de cobro.
- **IMPLEMENT**: `use-payments` (`useOrderPayments`, `useRegisterPayment` → invalida `["order",id]`); en `order-page`: sección "Cobrar" (Select medio + Input monto pre-cargado con el saldo, botón Registrar), lista de pagos (medio + monto + estado), y badge **PAGADA** cuando `status === "PAID"`. Visible para CASHIER/MANAGER/OWNER.
- **MIRROR**: `order-page` (sección agregar ítem), `use-orders`.
- **GOTCHA**: monto en pesos → ×100 a minor units; default = saldo pendiente (total − cobrado).
- **VALIDATE**: `npm run build`; recorrer el flujo.

### Task 10 — Tests frontend + cierre (flujo manual)
- **ACTION**: tests + validación final del cobro manual.
- **IMPLEMENT**: test `payments-api` (body de register), test de labels. `npm run lint && test && build`.
- **MIRROR**: `orders-api.test.ts`.
- **VALIDATE**: front verde; backend verde.

---

> **Tasks 11-13 — Integración REAL de MercadoPago.** Prerrequisito: MCP `mercadopago` autenticado + credenciales sandbox + webhook público. **La API exacta de MP se consulta desde el MCP** durante estas tareas.

### Task 11 — Backend: adapter `MercadoPagoGateway`
- **ACTION**: `app/infrastructure/payments/mercadopago_gateway.py` (implementa `PaymentGateway`); config MP.
- **IMPLEMENT**: `MercadoPagoGateway.charge()` crea la intención/preferencia de pago en MP (endpoint + payload **leídos del MCP**), guarda el id de MP en `external_ref`, y deja el `Payment` en **`PENDING`** (devuelve `init_point`/QR). Método `fetch_status(external_ref)` para el webhook. `config.py`: `MP_ACCESS_TOKEN`, `MP_WEBHOOK_SECRET` (env). En el container, **Selector** del gateway según el medio (`manual` vs `mercadopago`), igual que `email_sender`.
- **MIRROR**: `email_sender` Selector en `container.py`; `ConsoleEmailSender`/`SmtpEmailSender`; `PaymentGateway` port.
- **GOTCHA**: Access Token **solo por env**, nunca loguear; `httpx.AsyncClient`. Pago MP **nace `PENDING`** y NO marca la comanda `PAID` hasta el webhook. `RegisterPayment` con método MERCADOPAGO no concilia todavía (espera confirmación).
- **VALIDATE**: `mypy app`; prueba en **sandbox** (manual).

### Task 12 — Backend: webhook de confirmación MP
- **ACTION**: `app/presentation/api/v1/webhooks.py` → `POST /webhooks/mercadopago` (público, sin auth de usuario).
- **IMPLEMENT**: **verificar la firma** del webhook (`MP_WEBHOOK_SECRET`, formato según MCP); buscar el `Payment` por `external_ref`; consultar el estado real con `gateway.fetch_status`; confirmar (`CONFIRMED`) o fallar; **disparar la conciliación** (si los CONFIRMED cubren el total → `order.mark_paid()`). **Idempotente** (misma notificación 2 veces no duplica ni rompe). El `tenant_id` se deriva del `Payment` (no hay token) → setear el `tenant_context` con ese tenant antes de tocar la DB.
- **MIRROR**: routers + `RegisterPayment` (conciliación). Manejo de firma inválida → 401.
- **GOTCHA**: endpoint público ⇒ **validar firma sí o sí**; idempotencia por id de evento/`external_ref`; el webhook corre fuera de una sesión con tenant → setear `tenant_context` manualmente desde el `Payment`.
- **VALIDATE**: test (firma válida confirma + concilia; firma inválida 401; reenvío idempotente).

### Task 13 — Frontend: flujo de cobro MercadoPago
- **ACTION**: en `order-page`, soportar el medio MercadoPago.
- **IMPLEMENT**: al registrar un pago MERCADOPAGO, mostrar el **link/QR** (`init_point`) y el estado **Pendiente**; con el `useOrder`/`useOrderPayments` (refetch) el estado pasa a **Confirmado** / comanda **PAGADA** cuando llega el webhook. `PaymentDTO` gana `init_point`/`qr`.
- **MIRROR**: `order-page`, `use-payments`, `use-kds-orders` (patrón de refetch).
- **VALIDATE**: `npm run build`; flujo end-to-end en sandbox (con túnel para el webhook).

---

## Testing Strategy

### Unit / Integration
| Test | Input | Expected | Edge? |
|---|---|---|---|
| Registrar pago total | order total 3800, pago 3800 ARS | order → PAID | — |
| Pago parcial | total 3800, pago 1000 | order NO PAID; cobrado 1000 | sí |
| Dos pagos cubren total | 1000 + 2800 | order PAID | sí |
| Monto inválido | amount 0 / negativo | `InvalidPaymentAmount` (422) | sí |
| Pago en order cancelada | order CANCELLED | error | sí |
| `mark_paid` doble | order ya PAID | `InvalidOrderTransition` | sí |
| Aislamiento RLS | tenant B | no ve pagos de A | sí |

### Edge Cases Checklist
- [ ] Pago que excede el total (se acepta; order PAID — vuelto se maneja fuera del sistema en MVP)
- [ ] Order inexistente → `order_not_found`
- [ ] Rol incorrecto (WAITER/KITCHEN) → 403
- [ ] Moneda del pago = moneda de la order
- [ ] Suma de pagos con uno FAILED no cuenta para PAID

---

## Validation Commands
### Backend
```bash
cd backend
poetry run ruff check . && poetry run mypy app
poetry run alembic upgrade head    # (+ downgrade -1 && upgrade head)
poetry run pytest tests/unit tests/integration -q
```
### Frontend
```bash
npm run typecheck && npm run lint && npm run test && npm run build
```
### Manual
- [ ] Cajero abre una comanda SERVED → Cobrar → Efectivo $total → comanda **PAGADA**.
- [ ] Dos pagos parciales (QR + efectivo) suman el total → PAGADA. Otro tenant no ve nada.

---

## Acceptance Criteria
- [ ] Registrar pago(s) por medio + monto; al cubrir el total la comanda pasa a `PAID`.
- [ ] Pagos tenant-scoped con RLS; aislamiento verificado.
- [ ] `Money` (entero + ISO-4217) en montos; medio de pago discriminado.
- [ ] RBAC: CASHIER/MANAGER/OWNER cobran; WAITER/KITCHEN no.
- [ ] Port `PaymentGateway` definido con adapter manual (reales diferidos).
- [ ] backend ruff+mypy+pytest verdes; migración up/down; front tsc+lint+test+build verdes.

## Risks
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Expectativa de pasarelas reales | Media | Media | Decisión de alcance explícita arriba; port listo; adapters reales = rebanada con credenciales |
| Tocar el agregado `Order` (PAID) rompe Fase 2 | Baja | Media | PAID es estado aditivo; tests de Fase 2 deben seguir verdes |
| Conciliación parcial/redondeo | Baja | Media | Suma en minor units (enteros); criterio `cobrado ≥ total` |

## Notes
- Esta fase **NO** integra pasarelas reales (decisión de alcance). Deja el `PaymentGateway` port + `ManualPaymentGateway`; MP/QR/Payway + webhooks + conciliación batch + cola de excepciones = rebanada posterior (necesita credenciales/sandbox).
- Es la fuente de dato de **medios de pago / plata cobrada** que la Fase 9 (asesor) usará para "QR vs posnet de ayer", conciliación, etc.
- Próximo tras Fase 3: **Fase 4 — Facturación AFIP** (sobre el cobro).
