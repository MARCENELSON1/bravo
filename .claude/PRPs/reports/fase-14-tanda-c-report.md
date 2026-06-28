# Implementation Report: Fase 14 — Tanda C (ciclo por ÍTEM)

La pieza central del plan: mover el ciclo de cocina del `Order` al `OrderItem`,
habilitando **rondas múltiples + bump por ítem + estación/bar** con un solo cambio
de modelo de dominio. `Order.status` queda **derivado** de los ítems (mapea al enum
existente y nunca toca PAID/CANCELLED), por lo que floor / pagos / proyección de
ventas / AFIP siguen funcionando sin cambios.

## Tareas (C1–C5)

| # | Tarea | Estado |
|---|---|---|
| C1 | Dominio: `ItemStatus`/`Station`; `OrderItem` con status/station/sent_at/ready_at; `add_item` permitido salvo PAID/CANCELLED; `march`/`advance_item`/`_recompute_status`; wrappers backward-compat | ✅ |
| C2 | Migración `0012` aditiva + backfill (status desde la orden, station desde el producto, sent_at desde created_at); reversible | ✅ |
| C3 | `AddOrderItem(s)` snapshotea station + PENDING; `MarchOrder` (=SendOrder) con timestamp; `AdvanceItem` por ítem; `list_kds(station)` a nivel ítem; eventos `kds.changed` con `{station}` | ✅ |
| C4 | `Product.station` (alta + tabla); `Role.BAR`; KDS acepta KITCHEN/BAR/MANAGER/OWNER filtrando por estación (`?station=`) | ✅ |
| C5 | `StationBoard` (Cocina + Barra) con ítems, bump/recall por ítem, orden por antigüedad (`sent_at`), realce **rush**; rutas/nav/landing BAR; rondas + "Marchar" + edición por ítem PENDING en la comanda | ✅ |

## Decisiones / desviaciones

- **`Order.status` derivado, sin agregar `IN_PROGRESS`.** Se colapsa el estado
  multi-ítem al enum existente (OPEN/SENT/PREPARING/READY/SERVED) para no romper
  switches aguas abajo. Regla: todo PENDING→OPEN; todo SERVED→SERVED; todo
  READY/SERVED→READY; algún PREPARING→PREPARING; resto→SENT.
- **KDS sigue devolviendo órdenes-con-ítems** (cada ítem lleva status/station/sent_at);
  el front aplana a tickets por ítem (`kdsTickets`). Evita reescribir el contrato y
  mantiene la isolación en RLS. Bump por ítem vía `POST /orders/{id}/items/{itemId}/{action}`.
- **Métodos viejos de orden** (`send_to_kitchen`/`start_preparing`/…) se reescriben
  como wrappers que operan sobre todos los ítems → los endpoints y tests existentes
  siguen verdes.
- **`ItemNotPending`/`InvalidItemTransition`** nuevas (409). El test de Tanda B
  "editar tras marchar" ahora espera `item_not_pending`.
- **Batch idempotente:** `march` sólo corre si hay ítems PENDING (un replay no
  dispara `EmptyOrder`).
- **Edición de estación de un producto existente** no incluida (no hay endpoint de
  update de producto hoy) — diferida.

## Validación

| Nivel | Resultado |
|---|---|
| Backend ruff + mypy | ✅ limpio (262 archivos) |
| Backend pytest | ✅ 299 verdes |
| Migración 0012 up/down | ✅ `upgrade head` + `downgrade -1 && upgrade head` |
| Frontend tsc + eslint | ✅ limpio |
| Frontend vitest | ✅ 92 verdes (+5: `kdsTickets`, `advanceItem`, `kds(station)`) |
| Frontend build | ✅ |

## Pendiente de Fase 14

Tandas **D** (mover/unir mesas), **E** (cierre de caja/arqueo Z), **F** (impresión).
Plan en `.claude/PRPs/plans/fase-14-profundidad-operativa.plan.md`.
