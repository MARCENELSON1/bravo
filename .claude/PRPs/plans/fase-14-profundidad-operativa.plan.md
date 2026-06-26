# Plan: Fase 14 — Profundidad Operativa

## Summary
Cierra los **gaps de capacidad operativa** que hoy obligan al staff a "trabajar alrededor" del sistema (lo que lo
hace lento), por rol: **mozo** (rondas múltiples, editar/borrar ítem, modificadores, mover/unir mesas), **cocina**
(bump por ítem, orden por antigüedad, rush), **bar** (estación propia, hoy inexistente), **cajero** (cierre de caja /
arqueo Z, anular/reembolsar, propina, recibo, cobro rápido). Construye sobre **Fase 13 (Velocidad Operativa)** ya
mergeada (optimistic UI, grilla, KDS/floor en SSE, caja rápida/split). La pieza central es **mover el ciclo de cocina
del `Order` al `OrderItem`** (status por ítem) — el backbone que habilita rondas múltiples + bump por ítem + routing
por estación de una sola vez.

## User Story
Como **mozo/cocinero/barman/cajero** quiero que el sistema soporte los **flujos reales del servicio** (agregar rondas
a una mesa ya enviada, corregir un ítem, mandar el café a la barra y la comida a la cocina, marcar listo ítem por
ítem, cerrar la caja al final del turno) **sin tener que cancelar y rehacer ni llevar cuentas aparte**, para que el
sistema sea tan rápido y completo como el que ya usan y no lo rechacen.

## Problem → Solution
Hoy el motor es funcional pero le faltan operaciones que un local usa todo el tiempo → **se trabaja alrededor**
(cancelar comandas, recrear, escanear el salón a ojo, arquear en papel). Solución: agregar esas capacidades
respetando Clean Arch + multi-tenant + RLS, reusando la infra de Fase 13 (`EventBus`/SSE, read models, optimismo,
hook `useRealtimeInvalidate`). El cambio de fondo (ciclo por `OrderItem`) destraba tres features a la vez.

## Metadata
- **Complexity**: **XL** (cambio de modelo de dominio en el agregado `Order` + 2-3 migraciones con RLS + nuevo
  subsistema de caja + estación/bar + frontend amplio). **Se implementa por tandas mergeables** (A→F), no en una pasada.
- **Source PRD**: N/A (deriva del análisis de eficiencia operativa por rol en la conversación; opcional formalizar
  con `/prp-prd` después).
- **PRD Phase**: Fase 14 — Profundidad Operativa (sucede a Fase 13).
- **Estimated Files**: ~70 (≈45 backend, ≈25 frontend) repartidos en 6 tandas.

---

## UX Design

### Before
```
Mozo: mesa enviada (SENT) → NO puede agregar nada (bloqueado). Para otra ronda: cancela y rehace.
Cocina/Barra: TODO (café, tragos, comida) cae en un único KDS; avanza la orden ENTERA, no por ítem.
Cajero: escanea el salón a ojo buscando verdes; entra a cada comanda para cobrar; al cierre arquea en papel.
```

### After
```
Mozo: mesa abierta o ya en servicio → agrega ítems (PENDING) → "Marchar" → van a su estación.
      Edita/borra un ítem PENDING; mueve/une mesas; modificadores en chips.
Cocina (KITCHEN) y Barra (BAR): cada uno ve SOLO sus ítems; marca listo ÍTEM por ítem; recall; orden por antigüedad.
Cajero: filtro "a cobrar" + buscador de mesa; cobra desde el salón (slide-over); al final: arqueo Z (esperado vs real
        por medio de pago) y cierre de turno; anula/reembolsa; propina; recibo no fiscal.
Todos: cada rol cae en SU pantalla al loguear.
```

### Interaction Changes
| Touchpoint | Before | After | Notes |
|---|---|---|---|
| Agregar ronda a mesa enviada | imposible | agregar ítems PENDING + "Marchar" | ciclo por ítem |
| Estado de cocina | por orden | por **ítem** (PENDING→SENT→PREPARING→READY→SERVED) | bump/recall por ítem |
| Café/tragos vs comida | mismo KDS | **estación** (Cocina/Barra) por producto | `station` + 2 tableros |
| Encontrar mesas a cobrar | a ojo | filtro "a cobrar" + buscar mesa | floor |
| Cierre de turno | papel | **arqueo Z** (esperado vs contado por medio) | nuevo subsistema caja |
| Landing al loguear | Dashboard para todos | por rol (mozo→Mesas, cocina→KDS, barra→Barra, cajero→a-cobrar) | nav/router |

---

## Mandatory Reading
| Prio | File | Why |
|---|---|---|
| P0 | `backend/app/domain/order/entities.py` | `Order`/`OrderItem` + máquina de estados — núcleo del cambio a ciclo por ítem |
| P0 | `backend/app/domain/order/value_objects.py` | `OrderStatus` (StrEnum) → molde para `ItemStatus` y `Station` |
| P0 | `backend/app/application/order/use_cases.py` | use cases + helpers `_kds_changed`/`_floor_changed` (publican al `EventBus`) → molde para los nuevos |
| P0 | `backend/app/infrastructure/persistence/order_repo.py` | `list_kds`/`list_active`/`save` (delete+re-add de ítems) → adaptar a ítem-status + estación |
| P0 | `backend/app/infrastructure/persistence/models.py` | `OrderItemORM`/`ProductORM`/`PaymentORM` → columnas nuevas (status/station/sent_at, tip, cash_session_id) |
| P0 | `backend/app/domain/realtime/ports.py` + `infrastructure/realtime/memory_bus.py` | `EventBus`/`DomainEvent` — reusar para eventos por estación |
| P0 | `backend/app/presentation/api/v1/{orders,kds,floor,realtime,payments}.py` | routers + `require_roles` + SSE — extender, no reescribir |
| P0 | `backend/app/application/floor/use_cases.py` | read model `GetFloor` → molde para `GetCashReport` (arqueo) y la vista "a cobrar" |
| P0 | `backend/app/domain/payment/` (entities + use_cases) | pago + settle → tip, refund, reabrir, link a cash session |
| P0 | `backend/app/container.py` | wiring DI (`providers.Factory`/`Singleton`) — registrar lo nuevo |
| P0 | `backend/alembic/versions/0010_*`, `0011_*` | molde de migración con `ENABLE/FORCE RLS` + policy `tenant_isolation` + GRANTs |
| P0 | `backend/app/domain/user/value_objects.py` | `Role` (StrEnum) → agregar `BAR` |
| P1 | `frontend/src/features/orders/order-page.tsx` | comanda + `CobroSection` → editar ítems, marchar, slide-over de cobro |
| P1 | `frontend/src/features/kds/kds-page.tsx` + `hooks/use-kds-orders.ts` + `hooks/use-realtime.ts` | KDS → por ítem + por estación; reusar `useRealtimeInvalidate` |
| P1 | `frontend/src/features/floor/floor-page.tsx` + `hooks/use-floor.ts` | filtros "a cobrar"/buscar mesa, cobro rápido, mover/unir |
| P1 | `frontend/src/app/router.tsx` + nav-config + `src/auth/` guards | landing por rol |
| P1 | `frontend/src/api/*` + `services/services-{context,provider}.tsx` + `test/test-utils.tsx` | clientes inyectables (patrón de registro en 3 archivos) |

## External Documentation
| Topic | Source | Key Takeaway |
|---|---|---|
| Impresión térmica (Tanda F, diferida) | ESC/POS / `python-escpos`; o impresión web `window.print` con CSS `@media print` | Para MVP: **port `TicketPrinter`** + adapter "navegador" (CSS print) y/o ESC/POS por red; hardware real es follow-up |
| (resto) | patrones internos ya establecidos (Fase 13) | **No external research adicional.** SSE/optimismo/read models/migración RLS ya son molde interno |

> No external research needed para el grueso — usa patrones internos establecidos en Fase 13 y el motor (Fases 2-4).

---

## Patterns to Mirror

### ITEM_STATUS_ENUM (nuevo — MIRROR: `OrderStatus`)
```python
# app/domain/order/value_objects.py
class ItemStatus(StrEnum):
    PENDING = "PENDING"      # cargado, sin marchar
    SENT = "SENT"; PREPARING = "PREPARING"; READY = "READY"; SERVED = "SERVED"
    CANCELLED = "CANCELLED"

class Station(StrEnum):
    KITCHEN = "KITCHEN"; BAR = "BAR"
```

### ORDER_AGGREGATE_ITEM_LIFECYCLE (cambio central — MIRROR: métodos de negocio en `Order` que ya levantan DomainError)
```python
# app/domain/order/entities.py — OrderItem gana status/station/sent_at/ready_at; Order opera sobre ítems
@dataclass
class OrderItem:
    id: str; product_id: str; name: str; unit_price: Money; quantity: int
    note: str | None = None
    station: Station = Station.KITCHEN
    status: ItemStatus = ItemStatus.PENDING
    sent_at: datetime | None = None
    ready_at: datetime | None = None

@dataclass
class Order:
    # add_item ahora permitido salvo PAID/CANCELLED → habilita rondas múltiples
    def add_item(self, item: OrderItem) -> None:
        if self.status in (OrderStatus.PAID, OrderStatus.CANCELLED):
            raise InvalidOrderTransition()
        if item.unit_price.currency != self.currency: raise CurrencyMismatch()
        self.items.append(item)
    def march(self, now: datetime) -> list[OrderItem]:        # "marchar": PENDING→SENT
        pend = [i for i in self.items if i.status is ItemStatus.PENDING]
        if not pend: raise EmptyOrder()
        for i in pend: i.status = ItemStatus.SENT; i.sent_at = now
        self._recompute_status()
        return pend
    def advance_item(self, item_id: str, action: str, now: datetime) -> OrderItem: ...  # bump/recall por ítem
    def remove_item(self, item_id: str) -> None: ...          # solo PENDING
    def set_item_quantity(self, item_id: str, qty: int) -> None: ...   # solo PENDING
    def _recompute_status(self) -> None: ...  # OPEN si todo PENDING; IN_PROGRESS si hay SENT/PREPARING/READY; SERVED si todos served
```
**GOTCHA:** mantener `Order.status` (derivado de los ítems) para no romper `list_active`/floor/pagos; las transiciones
viejas (`send_to_kitchen`) se reescriben sobre `march`. RLS y multi-tenant intactos.

### USE_CASE_WITH_EVENTBUS (MIRROR: `SendOrder`/`AdvanceOrder` actuales)
```python
# publica al EventBus tras persistir; ahora el evento lleva la estación afectada
await self._orders.save(order)
for st in {i.station for i in marched}:
    await self._event_bus.publish(DomainEvent("kds.changed", tenant_id, {"station": st.value}))
await self._event_bus.publish(_floor_changed(order))
```

### DI_PROVIDER (MIRROR: `container.py` `add_order_items_batch`/`get_floor`)
```python
march_order = providers.Factory(MarchOrder, orders=order_repository, tenant_context=tenant_context, event_bus=event_bus)
get_cash_report = providers.Factory(GetCashReport, payments=payment_repository, cash=cash_session_repository, tenant_context=tenant_context)
```

### ALEMBIC_RLS_MIGRATION (MIRROR: `0010`/`0011`)
```python
# nueva tabla tenant-scoped → ENABLE + FORCE RLS + policy current_setting('app.tenant_id', true)::uuid + GRANTs a bravo_app
# columnas aditivas (order_items.status/station/sent_at, products.station, payments.tip_amount) → ALTER ... ADD COLUMN ... server_default
```

### READ_MODEL (MIRROR: `GetFloor`)
```python
# GetCashReport: agrega payments de la sesión por method (esperado) para comparar con lo contado; tenant-scoped
```

### FRONTEND_REALTIME_HOOK (MIRROR: `useKdsOrders`/`useFloor` + `useRealtimeInvalidate`)
```ts
export function useStationBoard(station: "KITCHEN"|"BAR") {
  const q = useQuery({ queryKey: ["kds", station], queryFn: () => kdsApi.list(station), refetchInterval: 20000 })
  useRealtimeInvalidate("kds", "kds.changed", `kds`)   // el cliente filtra por estación al refetch
  return q
}
```

### SERVICE_REGISTRATION (MIRROR: registro en 3 archivos)
```ts
// nuevos clientes (cashApi, etc.): services-context.ts (tipo) + services-provider.tsx (instancia) + test/test-utils.tsx (fake)
```

---

## Files to Change (orientativo, por tanda)

### Backend
| File | Action |
|---|---|
| `domain/order/value_objects.py` | UPDATE — `ItemStatus`, `Station` |
| `domain/order/entities.py` | UPDATE — `OrderItem` (status/station/timestamps), `Order` (march/advance_item/remove_item/set_qty/transfer/merge/_recompute_status) |
| `domain/order/exceptions.py` | UPDATE — `ItemNotFound`, `InvalidItemTransition`, `ItemNotPending` |
| `domain/order/repository.py` | UPDATE — `list_kds(station)`, helpers de ítem |
| `domain/product/entities.py` + repo | UPDATE — `station: Station` |
| `domain/user/value_objects.py` | UPDATE — `Role.BAR` |
| `domain/cashier/{entities,exceptions,repository}.py` | CREATE — `CashSession`, `CashCount`, ports |
| `domain/printing/ports.py` | CREATE — `TicketPrinter` port (Tanda F) |
| `application/order/use_cases.py` | UPDATE/CREATE — `MarchOrder`, `AdvanceItem`(bump/recall), `RemoveOrderItem`, `SetItemQuantity`, `UpdateItemNote`, `TransferOrder`, `MergeOrders`; `AddOrderItem(s)` ahora setea station+PENDING |
| `application/cashier/use_cases.py` + dtos | CREATE — `OpenCashSession`, `CloseCashSession`(arqueo), `GetCashReport`(Z) |
| `application/payment/use_cases.py` | UPDATE — `tip`, `RefundPayment`, `ReopenOrder`, link `cash_session_id` |
| `application/floor/use_cases.py` | UPDATE — flag/derivado para "a cobrar" (status SERVED) |
| `infrastructure/persistence/models.py` + `mappers.py` | UPDATE — columnas nuevas + `CashSessionORM`/`CashCountORM` |
| `infrastructure/persistence/{order_repo,product_repo,payment_repo,cash_repo}.py` | UPDATE/CREATE |
| `infrastructure/printing/{browser_ticket,escpos_ticket}.py` | CREATE — adapters (Tanda F) |
| `presentation/api/v1/{orders,kds,payments,cashier,printing}.py` | UPDATE/CREATE — endpoints + `require_roles` (incl. `BAR`) |
| `presentation/api/v1/realtime.py` | UPDATE — el stream ya reenvía todo; el cliente filtra por estación (sin cambio o `?station=`) |
| `presentation/schemas/{orders,cashier,payments}.py` | UPDATE/CREATE |
| `presentation/errors.py` + `main.py` + `container.py` + `config.py` | UPDATE — registrar excepciones/routers/wiring/flags |
| `alembic/versions/0012_item_lifecycle_station.py`, `0013_cash_sessions_tips.py` | CREATE — migraciones RLS |
| `tests/unit/*` + `tests/integration/*` | CREATE/UPDATE |

### Frontend
| File | Action |
|---|---|
| `src/api/types-operations.ts` | UPDATE — `ItemStatus`, `Station`, item.status/station, FloorTable filtros, tip |
| `src/api/{orders-api,cash-api,payments-api,printing-api}.ts` (+ tests) | UPDATE/CREATE |
| `src/hooks/{use-orders,use-kds-orders,use-floor,use-payments,use-cash}.ts` | UPDATE/CREATE |
| `src/features/orders/order-page.tsx` + `product-grid.tsx` | UPDATE — editar/borrar ítem, marchar, modificadores chips, stepper 44px, slide-over cobro |
| `src/features/kds/kds-page.tsx` (+ `station-board.tsx`) | UPDATE/CREATE — por ítem + por estación + orden por antigüedad + rush + botones grandes |
| `src/features/floor/floor-page.tsx` | UPDATE — filtro "a cobrar", buscar mesa, mover/unir, cobro rápido |
| `src/features/cashier/cash-session-page.tsx` | CREATE — apertura/cierre/arqueo Z |
| `src/app/router.tsx` + nav-config + `src/auth/*` | UPDATE — landing por rol + ruta Barra/Caja + rol BAR |
| `src/services/services-{context,provider}.tsx` + `test/test-utils.tsx` | UPDATE — registrar `cashApi`/etc. |
| `src/lib/*` (helpers puros) + tests | CREATE — arqueo (esperado por medio), etc. |

## NOT Building
- **Offline-first / PWA** → es **Tanda 3 de Fase 13** (no duplicar acá).
- **Impresión térmica con hardware real certificado** → Tanda F entrega el **port + adapter MVP** (web print / ESC-POS por red); drivers/marcas específicas, follow-up.
- **Split en cuentas separadas reales** (varios comprobantes por mesa) → se mantiene split por monto/ítem al cobrar (Fase 13 T7); multi-check verdadero, follow-up.
- **Permisos granulares** (más allá de roles) — sigue siendo RBAC por rol.
- **Liquidación de propinas / payroll** — solo se captura la propina en el pago.
- **Reservas/host como rol nuevo** — fuera de alcance (Fase 7 ya cubre reservas).

---

## Step-by-Step Tasks

> Orden por **impacto/esfuerzo** y dependencias. Cada **Tanda** es commiteable/mergeable `--no-ff`. Validar
> (`ruff`+`mypy`+`pytest` · `tsc`+`eslint`+`vitest`+`build`) al cierre de cada tanda.

### 🅰 Tanda A — Quick wins (orientación + caja UX) · bajo riesgo, se siente enseguida
- **A1 Landing por rol.** `ACTION`: en el árbol de rutas/guard, redirigir según rol al loguear (WAITER→`/app/floor`,
  KITCHEN→`/app/kds`, BAR→`/app/bar`, CASHIER→vista a-cobrar, OWNER/MANAGER→Dashboard). `MIRROR`: `auth/` guards +
  `router.tsx`. `VALIDATE`: cada rol cae en su pantalla.
- **A2 Floor: filtro "a cobrar" + buscar mesa.** `ACTION`: toggle "Solo a cobrar" (filtra `active_order.status==='SERVED'`)
  + input de búsqueda por número. `MIRROR`: `floor-page.tsx`. `VALIDATE`: el cajero ubica la mesa sin escanear.
- **A3 Targets táctiles.** `ACTION`: stepper +/− a `h-11 w-11`; botones KDS a `size` mayor. `MIRROR`: `product-grid.tsx`,
  `kds-page.tsx`. `VALIDATE`: build.
- **Tests:** front (filtro/búsqueda puros + guard). **Frontend-only.**

### 🅱 Tanda B — Edición de comanda (mozo)
- **B1 Backend: borrar/editar ítem PENDING + nota.** `ACTION`: `RemoveOrderItem`, `SetItemQuantity`, `UpdateItemNote`
  (solo ítems `PENDING`); endpoints `DELETE /orders/{id}/items/{itemId}`, `PATCH .../items/{itemId}`. `IMPLEMENT`:
  métodos en `Order` que validan estado del ítem; excepciones nuevas en `_STATUS_BY_TYPE`. `MIRROR`: `AddOrderItem` +
  `errors.py`. `GOTCHA`: idempotencia/optimismo — reusar ids de cliente (Fase 13 T1). `VALIDATE`: e2e (borrar PENDING
  ok; borrar SENT → error).
- **B2 Frontend: editar/borrar + modificadores chips.** `ACTION`: en la lista de ítems, +/−/borrar para PENDING; nota
  editable; modificadores como chips rápidos (sin sal, punto…). Optimista (Fase 13 T2). `MIRROR`: `order-page.tsx`,
  `use-orders.ts`. `VALIDATE`: vitest del hook + build.

### 🅲 Tanda C — Ciclo por ÍTEM: rondas múltiples + bump por ítem + estación/bar (la pieza central, XL)
- **C1 Dominio: ciclo a nivel `OrderItem`.** `ACTION`: `ItemStatus`/`Station`; `OrderItem` con status/station/
  sent_at/ready_at; `Order.add_item` permitido salvo PAID/CANCELLED; `march`, `advance_item`(bump/recall),
  `_recompute_status`. `MIRROR`: `ORDER_AGGREGATE_ITEM_LIFECYCLE`. `GOTCHA`: `Order.status` derivado para no romper
  floor/list_active/pagos. `VALIDATE`: unit exhaustivo (rondas, transiciones de ítem, recall, recompute).
- **C2 Migración 0012.** `ACTION`: `order_items` ADD `status`/`station`/`sent_at`/`ready_at`; `products` ADD `station`
  (server_default 'KITCHEN'). `MIRROR`: `ALEMBIC_RLS_MIGRATION`. `GOTCHA`: aditivo + backfill `status='SERVED'` para
  comandas viejas pagadas; `station` de ítems viejos = la del producto (o KITCHEN). `VALIDATE`: `alembic upgrade` +
  `downgrade -1 && upgrade head`.
- **C3 Use cases + repo + eventos.** `ACTION`: `MarchOrder`, `AdvanceItem`; `AddOrderItem(s)` snapshotea `station` del
  producto y marca `PENDING`; `order_repo` persiste status/station de ítems y `list_kds(station, item-level)`. Eventos
  `kds.changed` con `{station}`. `MIRROR`: use cases Fase 13 + `USE_CASE_WITH_EVENTBUS`. `VALIDATE`: e2e (marchar →
  el ítem aparece en el board de su estación; bump por ítem; ronda nueva a mesa en servicio).
- **C4 Producto: estación + rol BAR.** `ACTION`: `Product.station` (UI alta/edición); `Role.BAR`; `require_roles` del
  KDS acepta `KITCHEN/BAR/MANAGER/OWNER` filtrando por estación. `MIRROR`: products router + `rbac.py`. `VALIDATE`:
  un café va a BAR, una milanesa a KITCHEN.
- **C5 Frontend KDS por estación + ítem.** `ACTION`: `station-board` (Cocina y Barra) con ítems (no órdenes), bump/
  recall por ítem, **orden por antigüedad** (`sent_at`), flag/realce **rush**, sonido/timer ya existentes; botón
  "Marchar" en la comanda. `MIRROR`: `kds-page.tsx`, `useRealtimeInvalidate`. `VALIDATE`: tsc+eslint+vitest+build;
  manual (2 tableros separados).

### 🅳 Tanda D — Movimientos de mesa (mozo)
- **D1 Transferir + unir.** `ACTION`: `TransferOrder(order_id, to_table)` (reasigna `table_id`); `MergeOrders(src→dst)`
  (mueve ítems, cierra la origen). Endpoints + UI desde el plano (mover/unir). `MIRROR`: use cases + `floor-page`.
  `GOTCHA`: emitir `floor.changed` de ambas mesas. `VALIDATE`: e2e (mover libera la mesa origen, ocupa destino; unir
  junta ítems).

### 🅴 Tanda E — Caja profunda (cajero)
- **E1 Dominio caja + migración 0013.** `ACTION`: `CashSession`(opened_by, opening_float, status OPEN/CLOSED, closed_at)
  + `CashCount`(method, expected, counted); `payments.tip_amount` + `cash_session_id`. Tablas tenant-scoped con RLS.
  `MIRROR`: `ALEMBIC_RLS_MIGRATION`, Fase 2 (agregado padre+hijos). `VALIDATE`: migración up/down.
- **E2 Use cases caja.** `ACTION`: `OpenCashSession`(fondo), `GetCashReport`(esperado por medio = suma de pagos
  CONFIRMED de la sesión), `CloseCashSession`(guarda contado, calcula diferencia, cierra). `MIRROR`: `GetFloor` read
  model + settle. `VALIDATE`: e2e (abrir→cobrar varios medios→Z muestra esperado→cerrar con contado→diferencia).
- **E3 Anular/reembolsar + reabrir + propina + recibo.** `ACTION`: `RefundPayment`(status→REFUNDED, revierte
  proyección/inventario si aplica), `ReopenOrder`(PAID→en servicio, con permiso MANAGER/OWNER), `tip` en el cobro,
  `TicketPrinter` no fiscal (port + adapter web). `MIRROR`: payments use cases + Fase 9 hooks. `GOTCHA`: el refund
  debe deshacer el `SalesProjector`/`InventoryConsumer` (idempotente inverso). `VALIDATE`: e2e (reembolso saca de
  sale_facts; reabrir permite editar).
- **E4 Frontend caja.** `ACTION`: página **Caja** (apertura/cierre/arqueo Z con esperado vs contado por medio);
  **cobro rápido** desde el salón (slide-over `CobroSection`); botón anular/reembolsar; campo propina; "imprimir
  recibo". `MIRROR`: `order-page` CobroSection + Cult UI sheet. `VALIDATE`: build + manual.

### 🅵 Tanda F — Impresión térmica (cross, MVP)
- **F1 Port + adapters + ruteo.** `ACTION`: port `TicketPrinter`; adapter **web** (CSS `@media print`) y stub
  **ESC/POS por red**; al marchar, "imprimir comanda" por estación (cocina/barra) opcional detrás de flag. `MIRROR`:
  Selector por config (como gateways/LLM). `VALIDATE`: imprime una comanda de prueba por estación (web).

### 🔚 Cierre
- **Z. Reporte + memoria.** Completar reporte en `.claude/PRPs/reports/fase-14-profundidad-operativa-report.md`, mover
  el plan a `plans/completed/`, actualizar PRD/memoria.

---

## Testing Strategy

### Unit
| Test | Input | Expected | Edge? |
|---|---|---|---|
| `Order.add_item` tras servicio | order IN_PROGRESS | agrega PENDING (ronda nueva) | sí |
| `add_item` en PAID | order PAID | `InvalidOrderTransition` | sí |
| `march` sin pendientes | todos SENT | `EmptyOrder` | sí |
| `advance_item` bump/recall | READY→PREPARING | ok (recall) | sí |
| `remove_item` SENT | ítem ya marchado | `ItemNotPending` | sí |
| estación del ítem | producto BAR | item.station=BAR (snapshot) | sí |
| `GetCashReport` esperado | 3 pagos CASH/CARD | esperado por medio correcto | — |
| `CloseCashSession` diferencia | contado < esperado | diferencia negativa registrada | sí |
| `RefundPayment` | pago CONFIRMED | status REFUNDED + revierte sale_facts | sí |
| `TransferOrder` | mesa A→B | order.table_id=B; A libre | sí |

### Edge Cases Checklist
- [ ] Aislamiento RLS en `cash_sessions`/`cash_counts` (tenant A no ve B)
- [ ] Rondas múltiples no rompen `list_active`/floor
- [ ] KDS por estación: BAR no ve ítems de KITCHEN y viceversa
- [ ] Reembolso idempotente (no doble-revierte sale_facts/stock)
- [ ] Reabrir orden ya facturada (AFIP) — bloquear o avisar
- [ ] Rol BAR: RBAC correcto en cada endpoint
- [ ] Migraciones aditivas reversibles + backfill de ítems viejos

---

## Validation Commands
### Backend
```bash
cd backend
poetry run ruff check . && poetry run mypy app
poetry run alembic upgrade head      # 0012, 0013 (+ downgrade -1 && upgrade head c/u)
poetry run pytest tests/unit tests/integration -q   # ≥80% dominio/aplicación
```
EXPECT: ruff/mypy limpios; migraciones up/down; tests verdes (el LLM nunca se llama en tests).

### Frontend
```bash
cd frontend
npx tsc --noEmit && npx eslint src && npx vitest run && npx vite build
```
EXPECT: cero errores; tests verdes.

### Manual / E2E local
- [ ] Mozo: mesa en servicio → agrega ronda → "Marchar" → cocina/barra reciben **sus** ítems.
- [ ] Mozo: edita/borra un ítem PENDING; mueve y une mesas.
- [ ] Cocina/Barra: marcan listo **ítem por ítem**; recall; board ordenado por antigüedad.
- [ ] Cajero: filtro "a cobrar" + buscar mesa; cobra desde el salón; **arqueo Z** (esperado vs contado); reembolsa; propina; recibo.
- [ ] Cada rol cae en su pantalla al loguear. Otro tenant no ve nada de este.

## Acceptance Criteria
- [ ] **Mozo:** rondas múltiples a una orden ya enviada; borrar/editar ítem PENDING; modificadores; mover/unir mesas.
- [ ] **Cocina/Barra:** ciclo y **bump por ítem** + recall; **estación** separa cocina de barra; orden por antigüedad + rush.
- [ ] **Cajero:** **cierre de caja / arqueo Z** (esperado vs contado por medio); anular/reembolsar + reabrir; propina; recibo; cobro rápido + filtro a-cobrar + buscar mesa.
- [ ] **Transversal:** landing por rol; impresión térmica (MVP por estación).
- [ ] Multi-tenant + RLS en todo lo nuevo; migraciones up/down; backend ruff+mypy+pytest verdes; front tsc+eslint+vitest+build verdes.

## Completion Checklist
- [ ] Imita los patrones del repo (entidad/VO/exception/port/usecase/router/repo/migration/test)
- [ ] Errores `{code EN, message ES}` registrados en el handler
- [ ] Filtro `tenant_id` explícito + RLS en cada tabla nueva
- [ ] Plata en enteros (minor units); nunca float
- [ ] Frontend reusa http-client/DI/guards/TanStack/SSE/optimismo/Cult UI; UX en español
- [ ] Eventos por estación reusan el `EventBus` (no instanciar a mano)
- [ ] Autocontenido — sin búsquedas extra durante la implementación

## Risks
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Refactor a ciclo por ítem rompe floor/KDS/pagos | A | A | `Order.status` derivado + tests de regresión de Fase 2/13; Tanda C aislada y validada antes de seguir |
| Migración de ítems viejos (status/station) | M | M | Backfill explícito (SERVED + station del producto); aditivo + reversible |
| Reembolso desincroniza sale_facts/stock | M | A | Revertir proyección/consumo de forma **idempotente** (inverso del hook de settle) |
| Estación mal ruteada (café a cocina) | M | M | `station` snapshot al agregar el ítem + test por estación |
| Reabrir orden ya facturada (AFIP) | B | A | Bloquear/avisar si hay `Invoice` autorizada |
| Alcance XL en una pasada | A | M | 6 tandas mergeables; A/B son quick wins; C es el núcleo y va sola |

## Notes
- **Decisión central:** mover el ciclo de cocina al `OrderItem` destraba **3 features con un cambio** (rondas
  múltiples + bump por ítem + estación). Es el mayor riesgo y por eso la Tanda C va aislada y con tests fuertes.
- **Reuso máximo de Fase 13:** `EventBus`/SSE, `useRealtimeInvalidate`, optimismo + ids de cliente, read models
  (molde para arqueo), Selector por config (impresión/flags). Casi todo lo "nuevo" cuelga de infra ya probada.
- **Prioridad recomendada:** A (quick wins) → C (rondas/bump/estación, el dolor mayor) → E (cierre de caja) → B →
  D → F. (A y C/E son los que más "se sienten".)
- **Offline (Fase 13 Tanda 3)** sigue pendiente y es complementario (confiabilidad).
</content>
