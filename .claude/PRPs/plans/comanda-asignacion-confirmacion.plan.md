# Plan: Asignación de mozo por confirmación de pedido QR (Fase 2)

## Summary
Que **toda mesa QR modo Salón tenga un mozo dueño** y una **barrera humana anti-abuso**. Cuando un mozo **confirma** (marcha) un pedido QR `PENDING`, queda dueño de la sesión (`TableSession.waiter_id`). Se agrega una **bandeja "QR por confirmar"** con los pedidos QR sin confirmar, un caso de uso `AssignTableWaiter` (única vía de setear/actualizar el dueño) y **reasignación manual** (tomar una mesa huérfana / que el encargado reasigne). Depende de la Fase 1 (ya completa).

## User Story
Como **mozo** en salón, quiero **que al confirmar un pedido que entró por QR la mesa quede a mi cargo** (y ver los pedidos QR pendientes en un solo lugar), para **que ninguna mesa quede sin atención y ningún pedido llegue a la cocina sin que alguien lo valide**.

## Problem → Solution
Hoy un pedido QR nace con `waiter_id` = UUID nil (`self_order.py:_resolve_waiter` → `_CUSTOMER_WAITER_ID`, `self_order.py:40,176-179`) y `TableSession.waiter_id` se setea **una sola vez** al abrir, sin reasignación (`table_session/use_cases.py:44-55`). En modo Salón (`requires_confirmation=ON`) la orden queda `PENDING`/`OPEN` y **no hay bandeja** que muestre esos pedidos ni forma de darles dueño → mesas huérfanas. **Solución:** al marchar (`SendOrder`) asignar el confirmante como dueño de la sesión y de sus órdenes vivas; bandeja de pedidos QR `OPEN`; `AssignTableWaiter` reutilizable para reasignar.

## Metadata
- **Complexity**: Large (backend: dominio + 1 use case nuevo + `SendOrder` + repo/DTO + 3 rutas + DI + tests; mobile: bandeja + Confirmar + reasignar + strings)
- **Source PRD**: `.claude/PRPs/prds/comanda-lista-y-asignacion.prd.md`
- **PRD Phase**: Fase 2 — Asignación por confirmación
- **Depends**: Fase 1 (completa)
- **Estimated Files**: ~14

---

## Decisiones de diseño (con recomendación — confirmables)

| Decisión | Recomendación | Alternativa | Por qué |
|---|---|---|---|
| **Fuente de verdad del dueño** | `TableSession.waiter_id` (PRD) | campo nuevo en Order | La sesión ya es compartida QR/mozo/KDS/pago |
| **Que el aviso `order.ready` (Fase 1) llegue al confirmante** | `AssignTableWaiter` **también estampa `waiter_id` en las órdenes vivas** de la sesión (`orders.list_open_by_session`) | cambiar el emit de Fase 1 para resolver el dueño vía sesión | No re-toca la Fase 1 (ya testeada); el emit sigue usando `order.waiter_id`, que ahora refleja al dueño real |
| **Cuándo asigna el confirmar/marchar** | Solo si la sesión es **huérfana** (`waiter_id` None o nil sentinel) | siempre reasignar al que marcha | No "robar" una mesa que ya tiene dueño (Caso A intacto) |
| **Quién puede reasignar** | Cualquier `WAITER` **toma** una mesa **huérfana**; `MANAGER/OWNER` reasignan a cualquiera | solo encargado | Resuelve mesas sin dueño sin fricción; el override queda para gestión |
| **Endpoint de reasignación** | Bajo `orders` (`/orders/{id}/claim` y `/orders/{id}/assign-waiter`) operando sobre la sesión de la orden | router nuevo `table-sessions` | No hay router de `table-sessions` montado; evita infra nueva |
| **Filtro de la bandeja** | `status=OPEN` **+** `source=CUSTOMER_QR` | todos los OPEN | Es específicamente "QR por confirmar" |

> El único punto que "revisa" Fase 1 es indirecto: al estampar `order.waiter_id` en la confirmación, el `order.ready` existente ya apunta al mozo correcto **sin cambiar** el código de Fase 1.

---

## Mandatory Reading

| Priority | File | Lines | Why |
|---|---|---|---|
| P0 | `backend/app/application/order/self_order.py` | 40, 110-147, 176-179 | Cómo nace el pedido QR (`source=CUSTOMER_QR`, nil waiter, gate `send=not requires_confirmation`) |
| P0 | `backend/app/domain/table_session/entities.py` | 22-45 | `TableSession` (mutable) + `waiter_id:36`; agregar `assign_waiter()` |
| P0 | `backend/app/application/table_session/use_cases.py` | 32-56, 60-95 | Dónde se setea `waiter_id` (OpenSession) + molde de use case de sesión; agregar `AssignTableWaiter` |
| P0 | `backend/app/application/order/use_cases.py` | 315-350, 78-97 | `SendOrder` (a extender con `sessions`+`waiter_id`) + cómo la orden cuelga de `session_id` |
| P0 | `backend/app/domain/table_session/repository.py` | 27-50 | `get_by_id`/`get_open_by_table`/`save` |
| P0 | `backend/app/domain/order/repository.py` | 29 | `list_open_by_session` (para estampar órdenes vivas) + agregar `list_pending_qr` |
| P0 | `backend/app/presentation/api/v1/orders.py` | 47, 82, 256-263, 88-101 | `_FLOOR_ROLES`, DTO expone `source`, ruta `/send` (no propaga `user_id`), molde de rutas |
| P1 | `backend/app/application/customer/use_cases.py` | 137 | `AssignOrderCustomer` = patrón EXACTO a copiar (cargar agregado → mutar → save) |
| P1 | `backend/app/container.py` | 453, 478, 662, 670-685, 713, 780 | Repos base + providers de sesión + `assign_order_customer` (molde) + `send_order` (sin `sessions`) |
| P1 | `backend/app/infrastructure/persistence/order_repo.py` | 18-24, 99 | `_ACTIVE_STATUSES`/`_KDS_ITEM_STATUSES`, `list_open_by_session` (molde para `list_pending_qr`) |
| P1 | `backend/tests/integration/test_e2e_self_order.py` | (todo) | Helpers `_enable`, `_qr_token`, `_product`; extender con confirm-assign + bandeja |
| P1 | `backend/tests/unit/test_self_order_settings.py` | (todo) | Molde de unit test con fake in-file del repo + `FakeTenantContext` |
| P0 | `mobile/lib/features/floor/floor_page.dart` + `floor_providers.dart` | — | Dónde montar la bandeja "QR por confirmar" + patrón de repo/provider |
| P1 | `mobile/lib/features/order/order_repository.dart` | — | Dónde agregar `sendOrder`/`claim`/`assignWaiter`/`pendingQr` |

## External Documentation
Ninguna — patrones internos (use case + repo + ruta + Riverpod).

---

## Patterns to Mirror

### USE_CASE_ASSIGN (backend) — copiar de `AssignOrderCustomer`
```python
# SOURCE: backend/app/application/customer/use_cases.py:137
class AssignOrderCustomer:
    async def execute(self, *, tenant_id, order_id, customer_id):
        order = await self._orders.get_by_id(tenant_id, order_id)   # cargar agregado
        order.customer_id = customer_id                              # mutar
        await self._orders.save(order)                              # persistir
# Para el mozo: sessions.get_by_id → session.assign_waiter(wid) → sessions.save
#               + orders.list_open_by_session → o.waiter_id = wid → orders.save
```

### EVENT_PUBLISH_IN_USE_CASE (backend) — `SendOrder` ya publica post-save
```python
# SOURCE: backend/app/application/order/use_cases.py:326-350 (SendOrder.execute)
order = await self._orders.get_by_id(tenant_id, order_id)
order.march(utcnow())
await self._orders.save(order)
# publish kds.changed + floor.changed  ← acá se inserta la asignación al confirmante
```

### REPO_FILTER (backend) — molde `list_open_by_session` → `list_pending_qr`
```python
# SOURCE: backend/app/infrastructure/persistence/order_repo.py:99 (list_open_by_session)
# nuevo: WHERE status='OPEN' AND source='CUSTOMER_QR' (tenant-scoped, RLS)
```

### DTO ya expone source
```python
# SOURCE: backend/app/presentation/api/v1/orders.py:82  order_to_response(...) incluye source=order.source.value
```

---

## Files to Change

| File | Action | Justification |
|---|---|---|
| `backend/app/domain/table_session/entities.py` | UPDATE | Método `assign_waiter(waiter_id)` (mutación guardada, único punto) |
| `backend/app/application/table_session/use_cases.py` | UPDATE | `AssignTableWaiter` (session + órdenes vivas) |
| `backend/app/application/order/use_cases.py` | UPDATE | `SendOrder`: inyectar `sessions` + recibir `waiter_id`; asignar al confirmar si huérfana |
| `backend/app/domain/order/repository.py` | UPDATE | Port `list_pending_qr(tenant_id)` |
| `backend/app/infrastructure/persistence/order_repo.py` | UPDATE | Impl `list_pending_qr` (OPEN + CUSTOMER_QR) |
| `backend/app/application/order/use_cases.py` | UPDATE | `ListPendingQrOrders` (use case de la bandeja) |
| `backend/app/presentation/api/v1/orders.py` | UPDATE | `/send` propaga `identity.user_id`; `GET /orders/pending-qr`; `POST /orders/{id}/claim`; `POST /orders/{id}/assign-waiter` |
| `backend/app/container.py` | UPDATE | Factory `assign_table_waiter`, `list_pending_qr`; `send_order` con `sessions`; wiring de claim/assign |
| `backend/tests/unit/test_assign_table_waiter.py` | CREATE | Unit: asigna sesión + estampa órdenes vivas; no pisa dueño existente salvo override |
| `backend/tests/integration/test_e2e_self_order.py` | UPDATE | QR PENDING → confirmar → `session.waiter_id`=confirmante + `order.ready` le llega; bandeja lista los QR OPEN; claim/reassign |
| `mobile/lib/features/floor/pending_qr_repository.dart` | CREATE | Cliente de `GET /orders/pending-qr` + `POST /orders/{id}/send` (confirmar) |
| `mobile/lib/features/floor/pending_qr_tray.dart` | CREATE | Bandeja "QR por confirmar" (lista + botón "Confirmar") en el Piso |
| `mobile/lib/features/order/order_repository.dart` | UPDATE | `claim(orderId)` / `assignWaiter(orderId, waiterId)` |
| `mobile/lib/l10n/strings.dart` | UPDATE | Strings ES/EN de la bandeja/confirmar/asignar |

## NOT Building (queda para Fase 3/4)
- **Modo Autoservicio / pagar-primero / auto-asignación round-robin** → Fase 3.
- **Push real (APNs/FCM)** → Fase 4.
- **Selector de modo de la Carta QR en Ajustes** → Fase 3 (acá seguimos con el toggle `requires_confirmation` existente).
- **Asignación por sector** → futuro (no hay mapeo mozo↔sector).

---

## Step-by-Step Tasks

### Task 1: Dominio — `TableSession.assign_waiter`
- **ACTION**: En `entities.py`, agregar método `assign_waiter(self, waiter_id: str) -> None: self.waiter_id = waiter_id`. (Método por claridad/único punto; la entidad es mutable.)
- **GOTCHA**: no romper `OpenSession` (sigue seteando en el constructor).
- **VALIDATE**: unit de Task 8.

### Task 2: Use case — `AssignTableWaiter`
- **ACTION**: En `application/table_session/use_cases.py`, agregar `AssignTableWaiter` con `__init__(self, sessions, orders, tenant_context)` y `execute(*, tenant_id, session_id, waiter_id)`.
- **IMPLEMENT**: `session = await self._sessions.get_by_id(tenant_id, session_id)` (404 si no) → `session.assign_waiter(waiter_id)` → `sessions.save(session)`; luego `for o in await self._orders.list_open_by_session(tenant_id, session_id): o.waiter_id = waiter_id; await self._orders.save(o)` (para que el `order.ready` de Fase 1 apunte al dueño).
- **MIRROR**: `USE_CASE_ASSIGN`.
- **GOTCHA**: `waiter_id` debe ser un user real del tenant (validación opcional vía `users`; si se difiere, confiar en `identity`). No tocar órdenes PAID/CANCELLED (`list_open_by_session` ya trae solo activas).
- **VALIDATE**: Task 8.

### Task 3: `SendOrder` — asignar al confirmar (Caso B)
- **ACTION**: En `use_cases.py` `SendOrder`: agregar `sessions` al `__init__` y `waiter_id: str | None = None` a `execute`. Tras `save(order)` + publicar, si la orden tiene `session_id` y la sesión es **huérfana**, asignar al confirmante.
- **IMPLEMENT**: `if waiter_id and order.session_id: session = await self._sessions.get_by_id(tenant_id, order.session_id); if session and session.waiter_id in (None, _CUSTOMER_WAITER_ID): session.assign_waiter(waiter_id); await self._sessions.save(session); order.waiter_id = waiter_id; await self._orders.save(order)` (o delegar en `AssignTableWaiter` inyectado — preferible para no duplicar; ver Task 4 opción DI).
- **GOTCHA**: importar/compartir el sentinel `_CUSTOMER_WAITER_ID` (self_order.py:40) — moverlo a un lugar común (p.ej. `domain/order/value_objects.py`) o reexportar. Emitir la asignación **antes** de que la cocina termine, así el `order.ready` ya tiene el dueño.
- **VALIDATE**: integración Task 9.

### Task 4: Ruta `/send` propaga el confirmante + wiring
- **ACTION**: En `orders.py:256`, pasar `waiter_id=identity.user_id` al `send_order.execute(...)`. En `container.py`, sumar `sessions=table_session_repository` al Factory `send_order` (~780) y crear el Factory `assign_table_waiter` (junto a `assign_order_customer` ~713).
- **GOTCHA**: si `SendOrder` delega en `AssignTableWaiter`, inyectarlo como provider (Factory que recibe otro Factory) — patrón ya usado (`submit_customer_order` recibe `create_order`/`add_items_batch`, container.py:1430).
- **VALIDATE**: la app wirea (arranque/tests) sin errores.

### Task 5: Repo — `list_pending_qr`
- **ACTION**: Port en `order/repository.py`; impl en `order_repo.py` (WHERE `status='OPEN'` AND `source='CUSTOMER_QR'`, tenant-scoped).
- **MIRROR**: `list_open_by_session` (order_repo.py:99).
- **VALIDATE**: integración Task 9.

### Task 6: Use case + ruta bandeja "QR por confirmar"
- **ACTION**: `ListPendingQrOrders.execute(*, tenant_id)` → `orders.list_pending_qr(...)`; ruta `GET /orders/pending-qr` (`require_roles(*_FLOOR_ROLES)`) → `[order_to_response(o) ...]`. Factory `list_pending_qr` en container.
- **GOTCHA**: registrar la ruta **antes** de `GET /orders/{order_id}` para que `pending-qr` no matchee como `order_id` (o usar prefijo distinto).
- **VALIDATE**: integración Task 9.

### Task 7: Rutas de reasignación (claim / assign)
- **ACTION**: `POST /orders/{order_id}/claim` (FLOOR): asigna `identity.user_id` a la sesión de la orden **solo si huérfana** (si no, 409/decidir). `POST /orders/{order_id}/assign-waiter` (MANAGER/OWNER, body `{waiter_id}`): reasigna a cualquiera. Ambos resuelven `session_id` de la orden y llaman `AssignTableWaiter`.
- **GOTCHA**: para "claim" de mesa huérfana; el override de gestión no exige huérfana. Devolver la orden/estado actualizado.
- **VALIDATE**: integración Task 9.

### Task 8: Unit test `AssignTableWaiter`
- **ACTION**: Crear `tests/unit/test_assign_table_waiter.py` con fakes in-file de `TableSessionRepository` + `OrderRepository` + `FakeTenantContext`.
- **CASES**: asigna la sesión; estampa las órdenes vivas de la sesión; con sesión ya con dueño y flag "solo huérfana" no pisa (según Task 3); override reasigna.
- **MIRROR**: `test_self_order_settings.py` (fake in-file).
- **VALIDATE**: `pytest tests/unit/test_assign_table_waiter.py -q`.

### Task 9: Integración (extender `test_e2e_self_order.py`)
- **CASES**:
  1. `requires_confirmation=ON` → pedido QR queda OPEN; aparece en `GET /orders/pending-qr`.
  2. Un mozo hace `POST /orders/{id}/send` → la sesión queda con `waiter_id`=ese mozo y la orden también; ya no aparece en la bandeja.
  3. Avanzar a READY → el `order.ready` (SSE) trae `waiter_id`=el confirmante (prueba que el aviso de Fase 1 le llega).
  4. `POST /orders/{id}/claim` sobre mesa huérfana asigna al que llama; `assign-waiter` (manager) reasigna.
- **MIRROR**: helpers `_enable`, `_qr_token`, `_product`.
- **VALIDATE**: `pytest tests/integration/test_e2e_self_order.py -q`.

### Task 10: Mobile — bandeja "QR por confirmar" + Confirmar
- **ACTION**: `pending_qr_repository.dart` (`pendingQr()` → GET; `confirm(orderId)` → `POST /orders/{id}/send`); `pending_qr_tray.dart` (lista con mesa + ítems + botón "Confirmar"), montada en el Piso (sección arriba / badge). Provider con refetch por SSE `floor.changed`.
- **MIRROR**: repos/providers de floor existentes; patrón SSE listener de Fase 1.
- **GOTCHA**: al confirmar, refrescar bandeja + piso; el aviso de "listo" ya llega por Fase 1.
- **VALIDATE**: `flutter analyze` 0.

### Task 11: Mobile — reasignar / tomar mesa + strings
- **ACTION**: En la vista de mesa/orden, acción "Tomar mesa" (claim) para mesas huérfanas y "Cambiar mozo" (assign-waiter) para MANAGER/OWNER; métodos en `order_repository.dart`. Strings ES/EN.
- **GOTCHA**: gate por rol (claim = cualquier waiter en huérfana; assign = manager/owner).
- **VALIDATE**: `flutter analyze` 0 · `flutter test`.

---

## Testing Strategy

### Unit
| Test | Input | Expected |
|---|---|---|
| assign: sesión + órdenes | sesión huérfana + 1 orden OPEN | `session.waiter_id`=wid y `order.waiter_id`=wid |
| assign: no pisa dueño | sesión con dueño, sin override | no cambia (o cambia solo con override) |

### Integration
| Test | Expected |
|---|---|
| bandeja QR | `GET /orders/pending-qr` lista solo OPEN+CUSTOMER_QR |
| confirmar asigna | tras `/send`, `session.waiter_id`=confirmante; sale de la bandeja |
| aviso al dueño | `order.ready` trae `waiter_id`=confirmante |
| claim / reassign | claim toma huérfana; assign-waiter (manager) reasigna |

### Edge Cases
- [ ] Orden QR sin sesión abierta (nil) → confirmar la crea/asigna coherente
- [ ] Mesa ya con dueño (Caso A) → confirmar NO reasigna
- [ ] `pending-qr` no matchea la ruta `/{order_id}`
- [ ] Reasignar restampa las órdenes vivas (el aviso va al nuevo dueño)

---

## Validation Commands
```bash
cd /Users/marce/Desktop/BRAVO/backend && ruff check app tests && pytest tests/unit/test_assign_table_waiter.py tests/integration/test_e2e_self_order.py -q
cd /Users/marce/Desktop/BRAVO/mobile && flutter analyze && flutter test
```
EXPECT: verde. **`me.py` NUNCA stageado** (ruff lo auto-modifica).

### Manual (en vivo, prod dummy)
- [ ] Prender `requires_confirmation` (Ajustes) → pedir por QR → aparece en "QR por confirmar".
- [ ] Confirmar como mozo → la mesa queda a su nombre; al pasar a READY le llega el aviso de Fase 1.
- [ ] Tomar/reasignar una mesa huérfana.

---

## Acceptance Criteria
- [ ] Confirmar (marchar) un pedido QR deja `TableSession.waiter_id` = el mozo que confirmó (y estampa sus órdenes vivas).
- [ ] La bandeja "QR por confirmar" lista los pedidos QR `OPEN` y desaparecen al confirmarse.
- [ ] `AssignTableWaiter` es la única vía de setear/actualizar el dueño; hay claim (huérfana) + reassign (manager).
- [ ] El `order.ready` de Fase 1 le llega al confirmante (porque se estampó `order.waiter_id`).
- [ ] `ruff`/`pytest`/`flutter analyze`/`flutter test` verdes; sin regresiones.

## Completion Checklist
- [ ] Patrones del repo (use case cargar→mutar→save; repo filter; ruta FLOOR; Riverpod)
- [ ] Sentinel `_CUSTOMER_WAITER_ID` compartido (no duplicado)
- [ ] Multi-tenant: todo filtra por `tenant_id`
- [ ] Strings i18n ES/EN
- [ ] `me.py` NO stageado
- [ ] Sin scope de Fase 3/4 (nada de pagar-primero, push ni selector de modo)

## Risks
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Estampar `order.waiter_id` cambia semántica "creador" | Baja | Bajo | Solo en huérfanas / reasignación explícita; documentado |
| Ruta `pending-qr` colisiona con `/{order_id}` | Media | Medio | Declararla antes / prefijo propio (Task 6 gotcha) |
| `SendOrder` con más deps rompe wiring | Media | Medio | Task 4 cablea `sessions` + tests de wiring |
| Doble responsabilidad en `AssignTableWaiter` (sesión+órdenes) | Baja | Bajo | Es intencional: "dueño de la mesa" = sesión + comandas vivas |

## Notes
- Reusa la Fase 1 **sin tocarla**: al estampar `order.waiter_id` en la confirmación, el `order.ready` existente ya apunta al dueño correcto.
- La bandeja usa el `source` que el DTO ya expone (`orders.py:82`); no hace falta migración.
- Fase 3 (Autoservicio) reusará `AssignTableWaiter` para la auto-asignación al pagar.

---

*Generated: 2026-09-03 · Status: DRAFT — needs approval*
