# Plan: Cimiento `table_sessions` — la sesión de mesa como unidad de negocio

## Summary
Hoy la `Order` (comanda) **es** la sesión de mesa de facto: 1:1 con la mesa (`list_active` +
`setdefault` de la más vieja por `table_id`), timer desde `order.created_at`, floor binario
(OCCUPIED/FREE), cobro anclado en `payments.order_id`. Eso rompe timers (§1.1), deja mesas
fantasma (§1.2), e impide ticket-por-comensal, rotación y facturación por sector/mozo (§2, §12).

Introduce **`table_sessions` como aggregate nuevo e inmutable-al-cerrar** que **posee** el ciclo
de vida (timestamps, PAX, sector, mozo, status derivado, origin). Estrategia **strangler 1:1**:
cada orden abierta cuelga de una sesión (`orders.session_id` **nullable, 1:N desde el día 1**),
backfill 1:1 de las activas, y el floor pasa a leer sesiones. **Comanda/KDS/cobro NO cambian de
contrato** (ítems en `order_items.order_id`; cobro por `order_id`; arqueo por ventana temporal).
Paridad total: sin sector/PAX/sesión → comportamiento actual. Migración **0032**.

## La distinción crítica (no romper nada)
- **`table_sessions`** = eje **turno de mesa/negocio** (timestamps, PAX, sector, mozo, status
  derivado). Lo que lee el **floor**.
- **`Order`** = eje **contenedor de ítems/ronda**: sigue siendo el aggregate que la comanda/KDS
  editan y por el que se cobra.
- **1:1 hoy → 1:N mañana** vía `orders.session_id` (sin otra migración).
- **Paridad**: sin `session_id` (órdenes viejas) → fallback al comportamiento actual (timer por
  `order.created_at`, status por ítems de la orden).

## Decisiones (recomendación del plan)
1. **Entidad nueva** (no extender `Order`) — el spec pide entidad separada e inmutable; `Order`
   gana `session_id: str|None=None`. La sesión se crea/reusa al abrir la 1ª comanda de la mesa.
2. **Status DERIVADO en lectura** (como `Order._recompute_status`), a partir de timestamps
   almacenados + rollup de ítems. NO columna `status` editable en vivo (evita §1.3). Estados §4.2:
   libre / abierta / en_cocina / **para_servir (MÁXIMA PRIORIDAD)** / servida / a_cobrar / cerrada
   (precedencia: gana el que exige acción humana; `para_servir` > `en_cocina`).
3. **PAX + sector**: `table_sessions.pax` (default = `tables.capacity`), `sectors` **tabla**
   (nombre, color, sort_order), `tables.sector_id` nullable. Paridad: sin sector → floor plano;
   sin pax → sin badge.
4. **Rollout strangler**: migr 0032 crea todo nullable + RLS; **backfill 1:1** de órdenes activas
   (`opened_at=order.created_at`, `waiter_id`, `session_id`); órdenes cerradas quedan NULL.
   `CreateOrder` sigue creando sesión implícita si la mesa no tiene una abierta (paridad); el
   selector PAX+mozo es mejora aditiva de UI.
5. **`unit_cost` congelado por ítem → FUERA** (plan propio de costo por ítem).

## Slice A — Esquema + entidad + repo + backfill (invisible, paridad total)
- **Migración 0032** (patrón 0030 RLS): `SectorORM` + `TableSessionORM` (create_all); `tables +sector_id +capacity`; `orders +session_id` (index); GRANT + ENABLE/FORCE RLS + policy en tablas
  nuevas; **backfill 1:1** órdenes activas (INSERT…SELECT + UPDATE orders WHERE session_id IS NULL).
- **Back**: `domain/table_session/{entities,value_objects,repository,exceptions}.py` (`TableSession`,
  `SessionStatus`, `SessionOrigin`); `Table +sector_id +capacity`; `Order +session_id`; ORM +
  mappers (default-safe); `table_session_repo.py` + `sector_repo.py`; container providers.
- **Front**: ninguno. **Migr**: SÍ. **Riesgo/Tamaño**: M. **Paridad**: todo nullable + defaults.
- **Tests**: mapper round-trip; `Order` session_id=None (paridad); RLS aislamiento; backfill
  idempotente; `order_repo.add/save` preserva `session_id`.

## Slice B — Floor lee la sesión (status derivado + timers correctos)
- **Back**: `application/table_session/use_cases.py`: `OpenSession(table_id, pax, waiter_id)`,
  `SetSessionPax`, `RequestBill` (setea `bill_requested_at`), helper `derive_status(session, orders)`.
  `GetFloor` cruza `table_sessions` abiertas (no orders); `FloorTable +session` (status, opened_at,
  pax, mozo, `state_since` para el timer, sector); fallback mesa sin sesión → `libre`. `CreateOrder`
  resuelve/crea sesión + cuelga `session_id`; al marchar estampa `first_item_at`/`fired_at`; READY →
  `ready_at`. Endpoints `POST /floor/sessions`, `POST /floor/sessions/{id}/bill`, `PATCH .../pax`.
- **Front**: `FloorTableDTO +session`; `floor-page.tsx` estados renombrados (§5.2: "Lista"→"Para
  servir ⚡", "Preparando"→"En cocina"; sin verde para libre), **timer = `state_since`** (no
  created_at), badge PAX, selector PAX+mozo al tocar mesa libre (default capacity); chips "Para
  servir / A cobrar / Mis mesas / Libres" (aditivo); `useOpenSession`.
- **Migr**: NO. **Riesgo/Tamaño**: L (path más caliente). **Paridad**: mesa sin sesión → libre;
  1 orden por sesión → derive_status == rollup actual.
- **Tests**: `derive_status` (7 estados + precedencia para_servir); `GetFloor` con/sin sesión;
  timer por `state_since`; e2e READY en KDS → mesa `para_servir` <10s (SSE); chips (.test.ts).

## Slice C — Sectores como configuración (agrupación + facturación por sector)
- **Back**: `ListSectors`/`CreateSector`/`AssignTableSector`; `api/v1/sectors.py` + `PATCH
  /tables/{id}` (sector_id, capacity).
- **Front**: CRUD de sectores en Configuración (nombre/color/orden) + asignar sector/capacity;
  floor agrupa por sector plegable + subtotal + franja "Requieren atención" (§5.4) — solo si hay
  sectores. "Agregar mesa" se va a Config → Salón (§5.6).
- **Migr**: NO. **Riesgo/Tamaño**: M. **Paridad**: sin sectores → floor plano como hoy.

## Fuera de alcance (otros planes)
Bloque de control §7 (anular con motivo/`void_reasons`/`session_events`/PIN/descuentos/cortesías) ·
cursos §6.4 (`order_items.course`) · `unit_cost` congelado §3/§12 · turno de servicio §10.3
(`table_sessions.shift_id` queda nullable/diferido; `shifts` actual = fichaje, NO turno) ·
auto-cierre de sesión >30min (barrido, va con turno) · totales denormalizados al cerrar (columnas
en 0032 nullable, cálculo en el plan de cobro/cierre) · dividir/mover ítems, split de sesión,
`merged_into_id` activo, `customer_id` (CRM), `origin` real (col creada, default `salon`).

## Riesgos
- **Path caliente (floor + create/march)**: Slice A invisible (nullable+defaults); Slice B con
  fallback a libre/rollup actual; tests de paridad primero.
- **Doble fuente de status**: un solo helper `derive_status`, nunca columna editable en vivo.
- **Backfill**: idempotente (`WHERE session_id IS NULL`), solo activas.
- **Cobro por `order_id`**: no se toca; arqueo por ventana temporal igual.
- **`shifts` ambiguo**: `shift_id` del spec ≠ fichaje → nullable, diferido.

## Orden
A (esquema+backfill, migr 0032) → B (floor lee sesión) → C (sectores). Cada slice su rama + merge.

## Critical Files
- backend/app/infrastructure/persistence/models.py (`TableSessionORM`/`SectorORM`; `OrderORM.session_id`; `TableORM.sector_id/capacity`)
- backend/app/application/order/use_cases.py (`CreateOrder`/march estampan sesión + timestamps)
- backend/app/application/floor/use_cases.py (`GetFloor` cruza sesiones; `derive_status`)
- backend/app/infrastructure/persistence/mappers.py (mappers sesión/sector + extensión table/order default-safe)
- frontend/src/features/floor/floor-page.tsx (estados renombrados, timer por estado actual, PAX, selector al abrir)
