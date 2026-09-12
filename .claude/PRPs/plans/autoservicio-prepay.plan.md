# Plan: Autoservicio QR — pagar-primero + auto-asignación (Fase 3)

## Summary
Modo **Autoservicio** de la Carta QR: el comensal **paga primero** y la comanda **no llega a la cocina hasta que el pago se confirma**; al confirmarse (webhook), la orden **marcha** y se **auto-asigna** un mozo (round-robin entre fichados) con aviso "te asignaron la Mesa X". Se agrega un **selector de modo** (Salón / Autoservicio / Solo-lectura) que oculta los flags técnicos. Invierte el ciclo: el pago pasa a habilitar la cocina. Depende de Fase 1 (aviso) y Fase 2 (`AssignTableWaiter`), ambas completas.

## User Story
Como **comensal** en un local de quick-service, quiero **pedir y pagar desde el QR sin esperar al mozo**, y como **dueño** quiero **que ningún pedido llegue a la cocina sin estar pago y que igual quede un mozo a cargo**, para **habilitar autoservicio seguro sin mesas huérfanas**.

## Problem → Solution
Hoy el pedido QR o marcha directo (gate OFF) o espera confirmación de un mozo (gate ON, Fase 2). No existe "pagar-primero": `PayTableBill` cobra una orden **ya existente al final** y el webhook `ConfirmGatewayPayment._settle_order` sólo hace `order.mark_paid()` — **no marcha ni asigna**. → En modo Autoservicio la orden se **retiene** (PENDING, sin marchar) hasta que el pago confirmado dispara **marcha + auto-asignación**.

## Metadata
- **Complexity**: XL (backend: settings+migración, retención, inversión del webhook, round-robin con 2 métodos de repo nuevos, evento nuevo; mobile: selector de modo; web carta-QR: flujo prepago diferible)
- **Source PRD**: `.claude/PRPs/prds/comanda-lista-y-asignacion.prd.md` — Fase 3
- **Depends**: Fase 1, Fase 2
- **Estimated Files**: ~20

---

## Decisiones de diseño (recomendación — confirmables)

| # | Decisión | Recomendación | Por qué |
|---|---|---|---|
| 1 | **Modo QR** | Enum `SelfOrderMode` (SALON / AUTOSERVICIO / SOLO_LECTURA) **derivado** de flags; +1 columna `self_order_prepay_required`. SOLO_LECTURA = `enabled=false`; SALON = `enabled+requires_confirmation`; AUTOSERVICIO = `enabled+prepay_required` | La UX es un modo con descripción; el storage sigue siendo flags → Fase 1/2 intactas |
| 2 | **Marcar la orden retenida** | Nuevo valor `OrderSource.CUSTOMER_QR_PREPAID` (columna `source` es string libre → **sin migración de `orders`**) | Distingue la retenida por prepago de la PENDING de Salón; la bandeja "QR por confirmar" (`source=CUSTOMER_QR`) la excluye sola |
| 3 | **Checkout** | **Decoupled**: `SubmitCustomerOrder` retiene (`send=False`) y el response marca `prepay_required:true`; el comensal paga con el `POST /public/table/pay` **existente** (elige la orden retenida vía `_first_unpaid`, devuelve `checkout_url`) | Reusa el motor de pago sin tocarlo; separa órdenes de pagos |
| 4 | **Enganche de la inversión** | En `ConfirmGatewayPayment.execute`, **después** de `_settle_order`: si la orden es `CUSTOMER_QR_PREPAID` y sigue sin marchar → `SendOrder(waiter_id=auto)` (marcha + asigna + eventos) | El webhook ya tiene `OrderRepository`; un solo caso de uso marcha+asigna |
| 5 | **Auto-asignación** | `AutoAssignWaiter`: least-loaded entre **fichados** con Role=WAITER (menos mesas abiertas). Empate → menor `user_id` (determinista) | Usa el fichaje real; sin mapeo de sectores |
| 6 | **Sin mozo fichado** | Marcha **igual** (el comensal ya pagó), **sin asignar** → queda huérfana; un mozo la **toma** con `claim` (Fase 2) | El pago no puede quedar trabado por falta de mozo |
| 7 | **Aviso "te asignaron"** | Emitir evento `table.assigned` (payload waiter_id/table). Banner mobile reusando el patrón `ReadyAlert` (Fase 1) — **incluido si entra; si no, el evento queda listo para Fase 4/push** | Reusa la infra SSE; app-cerrada es Fase 4 |
| 8 | **UI del comensal (carta QR web, `frontend/`)** | **Tanda E, separable**: el backend queda validable por API; el flujo "submit→pagar" del comensal va en el web de la carta | Mantiene Fase 3 enfocada en backend + Ajustes mobile |

**Diferidos documentados (no bloqueantes):** TTL de una orden retenida sin pagar (hoy simplemente nunca marcha = la barrera anti-abuso); "1 orden = 1 pago" (rondas adicionales = órdenes prepagas nuevas).

---

## Mandatory Reading

| Priority | File | Lines | Why |
|---|---|---|---|
| P0 | `backend/app/domain/order/settings.py` | 7-27 | `SelfOrderSettings` (+`prepay_required`) + `SelfOrderMode` derivado |
| P0 | `backend/app/application/order/self_order.py` | 46-75, 113-151, 179-183 | `Update/GetSelfOrderSettings`; el gate `send=` (forzar False en prepay + `source` prepago) |
| P0 | `backend/app/application/payment/use_cases.py` | 37-78, 268-364 | `_settle_order` (transición PAID) + `ConfirmGatewayPayment` (constructor+execute) = **el enganche** |
| P0 | `backend/app/application/order/use_cases.py` | 316-356 | `SendOrder(waiter_id=...)` = marcha + asigna (a invocar desde el webhook) |
| P0 | `backend/app/application/table_session/use_cases.py` | 110-159 | `AssignTableWaiter` (reuso para asignar) |
| P0 | `backend/app/domain/timeclock/repository.py` | 9-32 | `ShiftRepository` (falta `list_open`) |
| P0 | `backend/app/infrastructure/persistence/shift_repo.py` | 28 | `get_open_for_user` = molde de `list_open` |
| P0 | `backend/app/domain/user/repository.py` | — | `UserRepository` (falta `list_by_role`/`list_active`) |
| P0 | `backend/app/domain/table_session/repository.py` + `..._repo.py` | 42-47 / 48-60 | `list_open` (contar mesas por mozo) |
| P1 | `backend/app/infrastructure/persistence/self_order_settings_repo.py` | 21-42 | Leer/escribir columnas en `tenants` (+ prepay) |
| P1 | `backend/alembic/versions/0049_self_pay.py` | 24-39 | Molde de migración: `op.add_column("tenants", ...)` + `server_default` |
| P1 | `backend/app/presentation/api/v1/self_order.py` + `schemas/self_order.py` | 26-52 | GET/PUT `/self-order/settings` (exponer `mode`) |
| P1 | `backend/app/presentation/api/v1/public_menu.py` | 210-233 | Response de `/public/table/order` (`prepay_required`) |
| P1 | `backend/app/domain/order/value_objects.py` | 55-66 | `OrderSource` (+`CUSTOMER_QR_PREPAID`) + sentinel |
| P1 | `backend/app/container.py` | 688, 788-791, 1098-1108, 1442-1454 | Providers `assign_table_waiter`/`send_order`/`confirm_gateway_payment`/`submit_customer_order` |
| P1 | `backend/tests/integration/test_e2e_webhook.py` | 27-84 | `FakeOnlineGateway` + override + POST `/webhooks/mercadopago` = molde del test estrella |
| P1 | `backend/tests/integration/test_e2e_timeclock.py` | — | Fichar mozos (clock-in) para el escenario round-robin |
| P1 | `mobile/lib/features/settings/*self_order*` / Ajustes Carta QR | — | Dónde va el selector de modo |

---

## Patterns to Mirror

### WEBHOOK_HOOK (backend) — enganche tras PAID
```python
# SOURCE: app/application/payment/use_cases.py:328-346 (ConfirmGatewayPayment.execute)
if status is CONFIRMED:
    payment.confirm(); await self._payments.save(payment)
    await _settle_order(...)          # marca PAID
    # ← Fase 3: si la orden es CUSTOMER_QR_PREPAID y sigue sin marchar:
    #   waiter = await self._auto_assign.execute(tenant_id=...)
    #   await self._send_order.execute(tenant_id=..., order_id=..., waiter_id=waiter)
```

### REPO_FILTER_OPEN (backend) — `list_open` de shifts
```python
# SOURCE: app/infrastructure/persistence/shift_repo.py:28 (get_open_for_user)
# nuevo: WHERE tenant_id=? AND status='OPEN'  (status indexado)
```

### SEND_MARCHES_AND_ASSIGNS (backend)
```python
# SOURCE: app/application/order/use_cases.py:333-352 (SendOrder.execute)
order.march(utcnow()); await self._orders.save(order)
if waiter_id and order.session_id:
    await self._assign_waiter.execute(..., only_if_unassigned=True, conflict_raises=False)
# publica kds.changed + floor.changed
```

### FAKE_ONLINE_GATEWAY (test)
```python
# SOURCE: tests/integration/test_e2e_webhook.py:27-84
# charge → PENDING + checkout_url + last_ref="<tenant>:<payment>"
# fetch_status → CONFIRMED con external_reference=last_ref
# override container.payment_gateway + mercadopago_gateway; POST _HOOK con _SIG
```

---

## Files to Change

| File | Action | Justification |
|---|---|---|
| `backend/app/domain/order/settings.py` | UPDATE | `prepay_required` + `SelfOrderMode` (derivado) |
| `backend/app/domain/order/value_objects.py` | UPDATE | `OrderSource.CUSTOMER_QR_PREPAID` |
| `backend/alembic/versions/0051_self_order_prepay.py` | CREATE | Columna `tenants.self_order_prepay_required` (default false) |
| `backend/app/infrastructure/persistence/self_order_settings_repo.py` | UPDATE | Leer/escribir `prepay_required` |
| `backend/app/infrastructure/persistence/models.py` | UPDATE | Columna `self_order_prepay_required` |
| `backend/app/application/order/self_order.py` | UPDATE | `Update/GetSelfOrderSettings` con modo; retención (`send=False`+`source` prepago) |
| `backend/app/presentation/api/v1/self_order.py` + `schemas/self_order.py` | UPDATE | Exponer/aceptar `mode` |
| `backend/app/presentation/api/v1/public_menu.py` + `schemas/public_menu.py` | UPDATE | `prepay_required` en el response del pedido |
| `backend/app/domain/timeclock/repository.py` + `infrastructure/.../shift_repo.py` | UPDATE | `list_open(tenant_id)` |
| `backend/app/domain/user/repository.py` + `infrastructure/.../user_repo.py` | UPDATE | `list_by_role(tenant_id, role)` |
| `backend/app/application/order/auto_assign.py` | CREATE | `AutoAssignWaiter` (round-robin least-loaded entre fichados) |
| `backend/app/application/payment/use_cases.py` | UPDATE | `ConfirmGatewayPayment`: marcha + auto-asigna la orden prepaga confirmada |
| `backend/app/domain/realtime/...` / event factory | UPDATE | Evento `table.assigned` |
| `backend/app/container.py` | UPDATE | Wiring: `auto_assign_waiter`, `confirm_gateway_payment` (deps nuevas), `submit_customer_order` |
| `backend/tests/unit/test_auto_assign_waiter.py` | CREATE | Round-robin: elige el fichado con menos mesas; fallback sin fichados |
| `backend/tests/integration/test_e2e_autoservicio.py` | CREATE | submit prepago (retenida) → pagar → webhook → SENT + asignada |
| `mobile/lib/features/settings/...` | UPDATE | Selector de modo (Salón/Autoservicio/Solo-lectura) con descripción |
| `mobile/lib/l10n/strings.dart` | UPDATE | Strings del selector + "te asignaron" |
| `frontend/` (carta QR) | **Tanda E (separable)** | Flujo del comensal: submit → pagar-primero |

---

## Step-by-Step Tasks (por tanda)

### Tanda A — Modo + settings + retención
1. **`SelfOrderSettings`+`SelfOrderMode`**: agregar `prepay_required: bool = False`; un `@property mode` (o función) que derive SALON/AUTOSERVICIO/SOLO_LECTURA de `(enabled, requires_confirmation, prepay_required)`.
2. **Migración 0051** `tenants.self_order_prepay_required` (Boolean, nullable=False, server_default="false") — molde `0049_self_pay.py`. `down_revision="0050_payment_idempotency"`.
3. **Repo/models**: sumar la columna a `models.py` + al `select`/`update` del repo.
4. **Update/GetSelfOrderSettings**: `UpdateSelfOrderSettings.execute` acepta `mode` (deriva los 3 flags) — mantener compat con `enabled`/`requires_confirmation` crudos si vienen. `Get` devuelve el `mode`.
5. **API**: `SelfOrderSettingsResponse` gana `mode` (+`prepay_required`); `UpdateSelfOrderSettingsRequest` acepta `mode`.
6. **`SubmitCustomerOrder`** (retención): si `settings.prepay_required` → crear la orden con `source=OrderSource.CUSTOMER_QR_PREPAID` y `send=False` (retenida, ítems PENDING). El response público marca `prepay_required=true`.
7. **Tests**: `test_e2e_self_order.py`/nuevo — modo autoservicio deja la orden OPEN retenida, NO marcha, y **no** aparece en `/orders/pending-qr`.

### Tanda B — Auto-asignación (repos + use case)
8. **`ShiftRepository.list_open(tenant_id) -> list[Shift]`** (port + impl SQL, `status='OPEN'`).
9. **`UserRepository.list_by_role(tenant_id, role) -> list[User]`** (o `list_active`) — para filtrar WAITER.
10. **`AutoAssignWaiter.execute(*, tenant_id) -> str | None`**: fichados ∩ WAITER; contar mesas abiertas por waiter (`sessions.list_open`, excluir None/sentinel); elegir el de menos mesas (empate → menor user_id); None si no hay.
11. **Unit test** `test_auto_assign_waiter.py`: elige el menos cargado; None sin fichados; ignora no-WAITER.

### Tanda C — Enganche del webhook (la inversión)
12. **`ConfirmGatewayPayment`**: inyectar `send_order: SendOrder` + `auto_assign: AutoAssignWaiter`. Tras `_settle_order`, si `order.source is CUSTOMER_QR_PREPAID` y la orden aún no marchó (tiene ítems PENDING) → `waiter = auto_assign.execute(...)`; `send_order.execute(tenant_id, order_id, waiter_id=waiter)`. (Idempotente: si ya marchó, no-op — `march` lanza `EmptyOrder` sin PENDING → guardar guard.)
13. **Evento `table.assigned`** (si hubo waiter): factory + publish por `EventBus` (payload waiter_id/table_id/table_number/order_id).
14. **Container**: extender `confirm_gateway_payment` con `send_order`, `auto_assign_waiter`; crear `auto_assign_waiter` provider (shifts+users+sessions+tenant_context).
15. **Integración** `test_e2e_autoservicio.py` (molde `test_e2e_webhook.py`+`test_e2e_timeclock.py`): fichar un mozo → modo autoservicio → submit (retenida) → `/public/table/pay` → POST `/webhooks/mercadopago` → la orden queda **SENT** y **asignada** al mozo fichado; con 0 fichados → SENT sin asignar.

### Tanda D — Mobile Ajustes (selector de modo)
16. **Selector de modo** en Ajustes Carta QR: 3 opciones con descripción (Salón = "el mozo confirma, se paga al final"; Autoservicio = "el comensal paga primero, se asigna solo"; Solo-lectura = "solo ver la carta"). Escribe `mode` vía PUT `/self-order/settings`. Strings ES/EN.

### Tanda E — Carta QR web (comensal, SEPARABLE)
17. En `frontend/` (carta QR): en modo autoservicio, tras enviar el pedido, ir directo al pago (reusa `/public/table/pay`). *Fuera del alcance del backend; el backend queda validable por API.*

---

## Testing Strategy
- **Unit**: `AutoAssignWaiter` (least-loaded, fallback, filtro WAITER); derivación de `SelfOrderMode`.
- **Integration** (estrella): fichar mozo → autoservicio → submit retenida (OPEN, no en pending-qr) → pay → webhook CONFIRMED → orden **SENT + asignada**; 0 fichados → SENT sin asignar; verificar que un pago que **no** confirma deja la orden retenida (no marcha).
- **Edge**: doble webhook (idempotente, no doble marcha); orden ya marchada; sin mozos fichados; prepay off (Salón/gate intactos → Fase 1/2 sin regresión).

## Validation Commands
```bash
cd backend && ruff check app tests && alembic upgrade head && pytest tests/unit/test_auto_assign_waiter.py tests/integration/test_e2e_autoservicio.py tests/integration/test_e2e_self_order.py tests/integration/test_e2e_webhook.py -q
cd mobile && flutter analyze && flutter test
```
EXPECT: verde. **`me.py` NUNCA stageado.** Migración 0051 aplica y revierte.

### Manual en vivo (prod dummy, con restore)
- [ ] Poner modo Autoservicio en bravo → pedir por QR → la orden NO aparece en cocina/KDS ni en "QR por confirmar".
- [ ] Pagar (gateway) → simular/confirmar webhook → la orden marcha (SENT) y queda asignada a un mozo fichado.
- [ ] Restaurar el modo original.

## Acceptance Criteria
- [ ] En Autoservicio la orden QR **no llega a la cocina** hasta el pago confirmado.
- [ ] Al confirmarse el pago, la orden **marcha** y queda **asignada** (mozo fichado) — o huérfana si no hay fichados.
- [ ] El selector de modo (3 opciones) escribe la config; Fase 1/2 sin regresión.
- [ ] Evento `table.assigned` emitido al asignar.
- [ ] `ruff`/`pytest`/migración/`flutter analyze`/`flutter test` verdes.

## Completion Checklist
- [ ] Migración 0051 reversible; `server_default` para paridad
- [ ] Idempotencia del webhook (no doble marcha)
- [ ] Multi-tenant en todo query nuevo (shifts/users/sessions)
- [ ] Fallback sin fichados documentado y testeado
- [ ] i18n ES/EN; `me.py` no stageado; sin scope de Fase 4 (push real)

## Risks
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| El webhook marcha dos veces (doble notificación MP) | Media | Medio | Guard: sólo si la orden aún tiene ítems PENDING; `march` idempotente |
| Round-robin sin fichados deja la mesa huérfana | Media | Bajo | Diseño explícito: marcha igual; `claim` (Fase 2) la recupera |
| Nuevos métodos de repo (shifts/users) sin usar en otros lados | Baja | Bajo | Sólo aditivos; tests propios |
| Cambiar el gate de `SubmitCustomerOrder` rompe Salón (Fase 2) | Media | Alto | `prepay_required` es un tercer flag; tests de no-regresión de gate ON/OFF |
| Acoplar pago a la orden | Baja | Medio | Decoupled: se reusa `/public/table/pay` sin tocar el motor |

## Notes
- Reusa Fase 1 (aviso `order.ready`) y Fase 2 (`AssignTableWaiter`, `claim`) sin romperlas.
- El backend queda validable por API (como Fase 2); la UI del comensal (Tanda E) es separable.
- "Te asignaron" en vivo = SSE (app abierta); app cerrada = Fase 4 (push).

---

*Generated: 2026-09-03 · Status: DRAFT — needs approval*
