# Plan: Aviso "comanda lista" (evento `order.ready` → SSE → modal al mozo)

## Summary
Cuando la cocina termina una comanda (la orden pasa a `READY`), emitir un evento de realtime `order.ready` y mostrarle al **mozo dueño** (con la app abierta) un **banner + modal** con qué lleva y a qué mesa. Reusa el event-bus/SSE que ya existe; no monta push (eso es la Fase 4). Cubre los Casos A/B/C (el aviso es agnóstico de cómo se creó la orden).

## User Story
Como **mozo** en pleno servicio, quiero **que la app me avise apenas la cocina termina mi comanda, con la lista de lo que llevo y a qué mesa**, para **servir rápido sin ir a chequear la cocina**.

## Problem → Solution
Hoy el estado `READY` existe pero **no avisa nada** (el mozo mira el Piso pasivamente) → el mozo recibe un **banner "Mesa N lista"** que abre un **modal** con la comanda, en el momento.

## Metadata
- **Complexity**: Large (backend 2 archivos + test; mobile 5 archivos + test; toca el parser SSE compartido)
- **Source PRD**: `.claude/PRPs/prds/comanda-lista-y-asignacion.prd.md`
- **PRD Phase**: Fase 1 — Aviso "comanda lista"
- **Estimated Files**: ~9

---

## UX Design

### Before
```
Cocina toca "Listo" (KDS)  →  el ítem queda READY
Mozo: no se entera. Camina hasta la cocina o mira el Piso ("para servir ⚡").
```

### After
```
Cocina toca "Listo" (último ítem) → orden READY → evento order.ready (SSE)
Mozo dueño (app abierta): aparece un BANNER "Mesa 5 lista · Ver"
  → toca "Ver" → MODAL (bottom sheet) con: Mesa 5 · 2× Milanesa (sin sal) · 1× Ensalada · nota
  → botón "Servido" (marca los ítems servidos) / cerrar.
```

### Interaction Changes
| Touchpoint | Before | After | Notes |
|---|---|---|---|
| Cocina marca "Listo" | solo actualiza KDS/Piso | además dispara aviso al mozo | mismo botón, sin cambio para cocina |
| Mozo | mira el Piso | recibe banner + modal | solo al mozo dueño (`waiter_id == userId`) |
| App cerrada | — | (Fase 4: push) | esta fase es solo app abierta (SSE) |

---

## Mandatory Reading

| Priority | File | Lines | Why |
|---|---|---|---|
| P0 | `backend/app/application/order/use_cases.py` | 274-350 | Helpers de eventos (`_kds_changed`/`_floor_changed`) + `AdvanceItem.execute` (dónde emitir) |
| P0 | `backend/app/domain/order/entities.py` | 140-156, 236-251 | `advance_item` + `_recompute_status` (dónde nace `READY`) |
| P0 | `backend/app/domain/realtime/ports.py` | 1-44 | `DomainEvent` (payload `dict[str,str]`) + `EventBus` |
| P0 | `backend/app/presentation/api/v1/realtime.py` | 21, 42-90 | `_STREAM_ROLES` (falta WAITER) + formato SSE (`event:`/`data:`) |
| P1 | `backend/app/application/public_menu/use_cases.py` | 153-195 | `floor.call` = molde de evento nuevo con payload enriquecido |
| P1 | `backend/app/container.py` | 411-413, 786-804 | `event_bus` Singleton + Factory de `advance_item`/`transfer_order` (mirror para inyectar `tables`) |
| P1 | `backend/tests/unit/test_table_attention.py` | 1-79 | Molde de test con `_SpyBus` + fakes inline |
| P0 | `mobile/lib/data/realtime/realtime_service.dart` | 16-63 | Cliente SSE; **hoy descarta `data:`** (a extender) |
| P0 | `mobile/lib/features/floor/floor_providers.dart` | 11-53 | Patrón listener SSE → acción; providers |
| P0 | `mobile/lib/features/kds/kds_providers.dart` | 20-52 | Segundo consumidor del `events()` (a actualizar por el cambio de firma) |
| P1 | `mobile/lib/features/cashier/cobro_sheet.dart` | 16-159 | Molde del bottom-sheet (`ConsumerStatefulWidget(orderId)` que observa la orden) |
| P1 | `mobile/lib/features/order/order_dtos.dart` | 6-157 | `Order`/`OrderItem`/`SelectedOption` para el modal |
| P1 | `mobile/lib/features/order/order_providers.dart` | 35-39, 154-157 | `orderControllerProvider(orderId)` para traer la comanda |
| P1 | `mobile/lib/features/kds/kds_page.dart` | 108-152 | Render real "cantidad × nombre / modificadores / nota" a calcar |
| P1 | `mobile/lib/features/shell/app_scaffold.dart` | 28-70 | Dónde montar el listener global (gateado por sesión) |

## External Documentation
No external research needed — usa patrones internos ya establecidos (event bus, SSE, Riverpod, bottom sheet).

---

## Patterns to Mirror

### EVENT_FACTORY (backend)
```python
# SOURCE: backend/app/application/order/use_cases.py:283-297
def _floor_changed_table(tenant_id: str, table_id: str) -> DomainEvent:
    return DomainEvent(type="floor.changed", tenant_id=tenant_id,
                       payload={"table_id": table_id})
# molde con payload enriquecido: public_menu/use_cases.py:153-195 (floor.call)
# payload es dict[str,str] → TODO valor casteado a str.
```

### EVENT_PUBLISH_IN_USE_CASE (backend)
```python
# SOURCE: backend/app/application/order/use_cases.py:338-350
item = order.advance_item(item_id, action, utcnow())   # _recompute_status corre acá
await self._orders.save(order)
for event in _kds_changed(order, {item.station}):
    await self._event_bus.publish(event)
await self._event_bus.publish(_floor_changed(order))
# publish SIEMPRE después de save(); order.status ya recalculado.
```

### USE_CASE_TEST_SPYBUS (backend)
```python
# SOURCE: backend/tests/unit/test_table_attention.py (inline fakes + _SpyBus)
class _SpyBus:
    def __init__(self) -> None: self.published: list[DomainEvent] = []
    async def publish(self, event: DomainEvent) -> None: self.published.append(event)
# assert bus.published[0].type == "floor.call"; asyncio_mode=auto (async def test_ corre directo)
```

### SSE_LISTENER_RIVERPOD (mobile)
```dart
// SOURCE: mobile/lib/features/floor/floor_providers.dart:33-44
_sse = ref.read(realtimeServiceProvider).events('floor').listen((event) {
  if (event == 'floor.changed') refresh();
});
ref.onDispose(() { _poll?.cancel(); _sse?.cancel(); });
```

### BOTTOM_SHEET (mobile)
```dart
// SOURCE: mobile/lib/features/order/order_page.dart:230-241
showModalBottomSheet<void>(
  context: context, isScrollControlled: true, showDragHandle: true,
  builder: (_) => SizedBox(
    height: MediaQuery.of(context).size.height * 0.85,
    child: CobroSheet(orderId: orderId)));
```

### COMANDA_RENDER (mobile)
```dart
// SOURCE: mobile/lib/features/kds/kds_page.dart:140-152
Text('${it.quantity}× ${it.name}');
if (it.selectedOptions.isNotEmpty) Text(it.selectedOptions.map((o) => o.name).join(', '));
if (it.note != null && it.note!.isNotEmpty) Text('› ${it.note}');
```

### DTO_PARSE (mobile)
```dart
// SOURCE: mobile/lib/features/order/order_dtos.dart:94-107  (snake_case → camelCase, listas anidadas)
selectedOptions: ((j['selected_options'] as List?) ?? const [])
    .map((e) => SelectedOption.fromJson(Map<String, dynamic>.from(e as Map))).toList(),
```

---

## Files to Change

| File | Action | Justification |
|---|---|---|
| `backend/app/application/order/use_cases.py` | UPDATE | Helper `_order_ready` + emitir en `AdvanceItem`/`AdvanceOrder` cuando `order.status is READY`; inyectar `tables` |
| `backend/app/presentation/api/v1/realtime.py` | UPDATE | Agregar `Role.WAITER` a `_STREAM_ROLES` (para que el mozo abra el stream) |
| `backend/app/container.py` | UPDATE | Inyectar `tables=table_repository` a `advance_item`/`advance_order` (mirror `transfer_order`) |
| `backend/tests/unit/test_order_ready_event.py` | CREATE | Test spy-bus: emite un `order.ready` solo cuando el último ítem completa la orden |
| `mobile/lib/data/realtime/realtime_service.dart` | UPDATE | Parsear `data:` y emitir `RealtimeEvent(name, data)` en vez de solo `String` |
| `mobile/lib/features/kds/kds_providers.dart` | UPDATE | Adaptar el listener al nuevo tipo (`event.name == 'kds.changed'`) |
| `mobile/lib/features/floor/floor_providers.dart` | UPDATE | Idem (`event.name == 'floor.changed'`) |
| `mobile/lib/features/order/comanda_lista_sheet.dart` | CREATE | El modal (bottom sheet) con la comanda + "Servido" |
| `mobile/lib/features/shell/ready_alert.dart` | CREATE | Listener global de `order.ready` (filtra por `userId`) → banner → abre el modal |
| `mobile/lib/features/shell/app_scaffold.dart` | UPDATE | Montar el listener global |
| `mobile/lib/l10n/strings.dart` | UPDATE | Strings del banner/modal |

## NOT Building
- **Push real (APNs/FCM)** — Fase 4. Esta fase es solo app abierta (SSE).
- **Asignación de mozo / bandeja QR** — Fase 2.
- **Filtrar por sesión de mesa** — el MVP filtra por `order.waiter_id == userId` (el que abrió la comanda), no por `TableSession.waiter_id`.
- **Marcar "servido" desde el modal como flujo nuevo** — reusar el avance de ítem existente; si complica, el botón "Servido" queda como Should.

---

## Step-by-Step Tasks

### Task 1: Backend — helper `_order_ready` + emisión
- **ACTION**: En `backend/app/application/order/use_cases.py`, agregar el helper y emitir en `AdvanceItem.execute` y `AdvanceOrder.execute`.
- **IMPLEMENT**:
  ```python
  def _order_ready(order: Order, table_number: str) -> DomainEvent:
      return DomainEvent(type="order.ready", tenant_id=order.tenant_id, payload={
          "order_id": order.id, "table_id": order.table_id,
          "table_number": table_number, "waiter_id": order.waiter_id or ""})
  ```
  En `AdvanceItem.execute`, tras los `publish` existentes (línea ~349): `if order.status is OrderStatus.READY: table = await self._tables.get_by_id(tenant_id, order.table_id); await self._event_bus.publish(_order_ready(order, str(table.number) if table else ""))`. Idem en `AdvanceOrder.execute` (~388).
- **MIRROR**: `EVENT_FACTORY` + `EVENT_PUBLISH_IN_USE_CASE`.
- **IMPORTS**: `OrderStatus` ya está importado (línea 19). `DomainEvent` ya usado.
- **GOTCHA**: `payload` es `dict[str,str]` → castear todo a `str`. Emitir **solo** cuando `order.status is READY` (no en cada ítem) para no spamear. `AdvanceItem` hoy NO tiene `self._tables` → agregarlo en el `__init__` (Task 3).
- **VALIDATE**: el test de Task 4 verifica un único `order.ready` al completar.

### Task 2: Backend — habilitar al WAITER en el stream
- **ACTION**: En `backend/app/presentation/api/v1/realtime.py:21`, agregar `Role.WAITER`.
- **IMPLEMENT**: `_STREAM_ROLES = (Role.WAITER, Role.KITCHEN, Role.MANAGER, Role.OWNER)`.
- **MIRROR**: la tupla existente.
- **GOTCHA**: sin esto, `POST /realtime/token` del mozo devuelve 403 y nunca abre el stream (el aviso no le llega). `Role` ya importado.
- **VALIDATE**: un mozo puede `POST /realtime/token` → 200.

### Task 3: Backend — DI de `tables` en `advance_item`/`advance_order`
- **ACTION**: En `backend/app/container.py`, agregar `tables=table_repository` a los Factory `advance_item` y `advance_order`; agregar `tables` al `__init__` de `AdvanceItem`/`AdvanceOrder`.
- **IMPLEMENT**: mirror de `transfer_order` (container.py:798-804, que ya recibe `tables=table_repository`).
- **MIRROR**: `transfer_order` provider.
- **GOTCHA**: el `__init__` de ambos casos de uso debe aceptar `tables` (guardar `self._tables`).
- **VALIDATE**: la app arranca (`uvicorn`/tests) sin errores de wiring.

### Task 4: Backend — test del evento
- **ACTION**: Crear `backend/tests/unit/test_order_ready_event.py`.
- **IMPLEMENT**: `_SpyBus` + `_FakeOrders` (dict con `get_by_id`/`save`) + `_FakeTables` inline; construir una orden con 2 ítems SENT; avanzar item 1 → ready (no debe emitir `order.ready`); avanzar item 2 → ready (debe emitir exactamente un `order.ready` con payload correcto).
- **MIRROR**: `USE_CASE_TEST_SPYBUS` (test_table_attention.py).
- **GOTCHA**: `asyncio_mode=auto` → `async def test_` corre directo, sin decorador. Los fakes van inline.
- **VALIDATE**: `pytest backend/tests/unit/test_order_ready_event.py` pasa.

### Task 5: Mobile — extender el parser SSE a `(name, data)`
- **ACTION**: En `mobile/lib/data/realtime/realtime_service.dart`, capturar la línea `data:` y emitir un record/clase `RealtimeEvent{ String name; Map<String,dynamic> data }` en vez de `String`. Cambiar el tipo de retorno de `events()` a `Stream<RealtimeEvent>`.
- **IMPLEMENT**: en el loop de parseo (líneas 37-56): acumular `data` cuando `line.startsWith('data:')` (`dataBuf = line.substring(5).trim()`), y al llegar la línea vacía hacer `yield RealtimeEvent(eventName!, dataBuf.isEmpty ? {} : jsonDecode(dataBuf))`. `import 'dart:convert'`.
- **MIRROR**: el parser existente (solo se agrega la rama `data:`).
- **GOTCHA**: rompe la firma → hay que actualizar los 2 consumidores (Task 6). Envolver `jsonDecode` en try/catch (payload puede venir vacío en un evento sin data).
- **VALIDATE**: `flutter analyze` 0.

### Task 6: Mobile — adaptar los listeners existentes
- **ACTION**: En `kds_providers.dart:31` y `floor_providers.dart:40`, cambiar `if (event == 'kds.changed')` → `if (event.name == 'kds.changed')` (idem floor).
- **MIRROR**: el patrón existente.
- **GOTCHA**: solo cambia `.name`; el resto igual.
- **VALIDATE**: `flutter analyze` 0; los tests de kds/floor siguen pasando.

### Task 7: Mobile — el modal `ComandaListaSheet`
- **ACTION**: Crear `mobile/lib/features/order/comanda_lista_sheet.dart` — `ConsumerStatefulWidget` que recibe `orderId` + `tableNumber` y observa `orderControllerProvider(orderId)`.
- **IMPLEMENT**: `showDragHandle`, título "Mesa N lista", lista de `order.liveItems` con `${it.quantity}× ${it.name}` + modificadores + nota (mirror `COMANDA_RENDER`), envuelto en `GlassPanel`. Botón "Servido" (Should: avanza los ítems `READY→SERVED` reusando el endpoint de avance; si complica, dejarlo como cerrar).
- **MIRROR**: `BOTTOM_SHEET` + `cobro_sheet.dart`.
- **IMPORTS**: `order_dtos.dart`, `order_providers.dart`, `ui/glass_panel.dart`, `l10n/strings.dart`.
- **GOTCHA**: usar `orderControllerProvider(orderId)` para traer la comanda fresca (el payload solo trae ids).
- **VALIDATE**: abre y muestra los ítems reales de una orden.

### Task 8: Mobile — listener global `ReadyAlert`
- **ACTION**: Crear `mobile/lib/features/shell/ready_alert.dart` — un widget/hook que se suscribe a `events('floor')`, filtra `event.name == 'order.ready' && data['waiter_id'] == session.userId`, y muestra un **MaterialBanner/SnackBar** "Mesa N lista · Ver" cuya acción abre `ComandaListaSheet`.
- **IMPLEMENT**: `ConsumerStatefulWidget` que en `initState` arranca la suscripción (o un `Notifier`), guarda el `StreamSubscription`, lo cancela en dispose. Al recibir el evento: `ScaffoldMessenger.of(context).showMaterialBanner(...)` con acción "Ver" → `showModalBottomSheet(ComandaListaSheet(orderId: data['order_id'], tableNumber: int.tryParse(data['table_number'] ?? '')))`.
- **MIRROR**: `SSE_LISTENER_RIVERPOD`.
- **IMPORTS**: `realtime_service` (via `realtimeServiceProvider` de floor_providers), `session_notifier`, `comanda_lista_sheet.dart`.
- **GOTCHA**: filtrar por `userId` (no por rol) — así el aviso llega al dueño real de la orden (mozo/manager/owner que la abrió) y no a cocina. Debouncear si llegan varios seguidos.
- **VALIDATE**: al emitir `order.ready` con `waiter_id` = usuario logueado, aparece el banner.

### Task 9: Mobile — montar el listener + strings
- **ACTION**: Envolver el body de `AppScaffold` (o el Scaffold) con `ReadyAlert` para que el banner aparezca en cualquier tab. Agregar strings en `strings.dart`.
- **IMPLEMENT**: en `app_scaffold.dart`, envolver el `Scaffold`/body. Strings: `readyBannerTitle(int mesa)` = "Mesa N lista", `readyBannerAction` = "Ver", `comandaListaTitle`, `served` (reusar si existe).
- **MIRROR**: montaje existente en `AppScaffold`.
- **GOTCHA**: montar una sola instancia (no por tab). Solo para sesiones autenticadas.
- **VALIDATE**: `flutter analyze` 0; el banner aparece estando en cualquier tab.

---

## Testing Strategy

### Unit Tests
| Test | Input | Expected Output | Edge Case? |
|---|---|---|---|
| backend: primer ítem ready | orden 2 ítems, avanzar 1 a ready | NO se publica `order.ready` (orden aún PREPARING) | sí |
| backend: último ítem ready | avanzar el 2º a ready | 1 `order.ready` con `order_id/table_id/waiter_id/table_number` | sí |
| backend: AdvanceOrder ready | `POST /orders/{id}/ready` | 1 `order.ready` | — |
| mobile: parse payload | frame `event: order.ready\ndata: {json}` | `RealtimeEvent(name:'order.ready', data:{...})` | sí (data vacío) |
| mobile: filtro por waiter | payload.waiter_id ≠ userId | no muestra banner | sí |

### Edge Cases Checklist
- [ ] Orden con un solo ítem (ready inmediato → un evento)
- [ ] Ítem `recall` (READY→PREPARING) no debe re-disparar al re-avanzar
- [ ] `data:` vacío / evento sin payload (kds.changed) → no rompe el parser
- [ ] Mozo distinto del dueño → no ve el banner
- [ ] SSE se corta y reconecta (ya lo maneja el retry de 3s)

---

## Validation Commands

### Static Analysis
```bash
cd /Users/marce/Desktop/BRAVO/mobile && flutter analyze
cd /Users/marce/Desktop/BRAVO/backend && ruff check app tests   # (o el linter del proyecto)
```
EXPECT: cero issues (ver gotcha: nunca stagear `me.py` que ruff auto-modifica).

### Unit Tests
```bash
cd /Users/marce/Desktop/BRAVO/backend && pytest tests/unit/test_order_ready_event.py -q
cd /Users/marce/Desktop/BRAVO/mobile && flutter test
```
EXPECT: todos pasan.

### Full Test Suite
```bash
cd /Users/marce/Desktop/BRAVO/backend && pytest -q
cd /Users/marce/Desktop/BRAVO/mobile && flutter test
```
EXPECT: sin regresiones.

### Manual Validation
- [ ] Loguearse como mozo en el simulador; abrir una comanda con ítems.
- [ ] Desde otro rol (cocina) marcar todos los ítems "Listo" en el KDS.
- [ ] Verificar que al mozo le aparece el banner "Mesa N lista · Ver" y el modal con los ítems correctos.

---

## Acceptance Criteria
- [ ] Backend emite un único `order.ready` cuando la orden pasa a `READY` (por KDS-item y por `/orders/{id}/ready`).
- [ ] El WAITER puede abrir el stream SSE.
- [ ] Mobile parsea el `data:` del SSE sin romper los listeners de kds/floor.
- [ ] El mozo dueño recibe el banner + modal con la comanda real; otro rol/mozo no.
- [ ] `flutter analyze` 0 · `flutter test` verde · `pytest` verde.

## Completion Checklist
- [ ] Sigue los patrones descubiertos (event factory, publish post-save, SSE listener, bottom sheet)
- [ ] Errores/naming según convención del repo
- [ ] Tests nuevos (backend spy-bus + mobile parse/filtro)
- [ ] `payload` todo string (backend)
- [ ] Sin valores hardcodeados; strings i18n ES/EN
- [ ] `me.py` NO stageado (ruff lo modifica solo)
- [ ] Sin scope extra (nada de push ni asignación)

## Risks
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Cambiar la firma de `events()` rompe kds/floor | Media | Medio | Task 6 actualiza ambos consumidores + tests |
| El mozo no tiene stream abierto (rol bloqueado) | Alta si se olvida | Alto | Task 2 agrega `WAITER` a `_STREAM_ROLES` |
| Banner intrusivo mid-servicio | Baja | Bajo | Banner con acción "Ver" (no modal automático); debounce |
| Query extra de `tables` por cada `ready` | Baja | Bajo | Solo cuando `order.status is READY` (1 vez por orden) |
| Multi-worker: el event bus in-memory no cruza procesos | Baja (MVP single-worker) | Medio | Documentado; futuro adapter Postgres LISTEN/NOTIFY detrás del mismo port |

## Notes
- El aviso es **agnóstico de cómo se creó la orden** → cubre A/B/C sin lógica extra.
- Filtramos por `order.waiter_id == userId` (el que abrió la comanda). En la Fase 2, cuando exista asignación por sesión, se puede migrar a `TableSession.waiter_id`.
- El `data:` del SSE ya lo emite el backend (`realtime.py:58`); el único cambio cliente es dejar de descartarlo.
- No hay push en esta fase: si el mozo tiene la app cerrada, no le llega (fallback pasivo = el Piso). Eso lo resuelve la Fase 4.
