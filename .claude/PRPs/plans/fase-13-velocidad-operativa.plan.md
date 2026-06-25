# Plan: Fase 13 — Velocidad Operativa (captura instantánea)

## Summary
Fase **transversal de performance + UX operativa**: llevar la **captura** (comanda del mozo, manejo de mesas, caja,
KDS) a **paridad o mejor** con los incumbentes (Fudo/MaxiRest/MrComanda) en *velocidad percibida*. No agrega un
módulo de negocio nuevo: **endurece y acelera** el motor ya construido (Fases 2–4) sobre la Clean Arch + multi-tenant
+ RLS existentes. El objetivo no es ganar en POS (ahí no está el diferencial), sino **no perder la adopción**: el
mozo/cajero usa la captura cientos de veces por día; si es más lenta que lo que ya usan, rechazan el sistema el día 1
y **nunca llegamos a venderles la inteligencia** (asesor Fase 9 + copiloto Fase 11), que es donde sí ganamos.

> **Posición en el roadmap:** se numera **Fase 13** pero es **PRIORITARIA**: corre **antes de 10 (Reportes/WhatsApp)
> y 12 (CRM)**. Razón: velocidad de captura = **puerta de adopción** (necesaria, no diferenciadora). Sin esto, el
> resto del valor no se llega a usar. Origen: feedback directo de un dueño de restaurante — "elige su sistema actual
> por lo rápido que es operativamente (comandas, mesas, caja, KDS)".

## Diagnóstico (estado actual, medido sobre el código)
El motor es funcional pero **MVP-grade en velocidad percibida**. Todo lo que hace lento a un POS está presente:

| Síntoma | Hoy | Evidencia |
|---|---|---|
| Cada tap espera al servidor (spinner) | Sin optimistic UI en ningún lado | `frontend/src/hooks/use-orders.ts:32-54`, `use-payments.ts:15-24` |
| Cocina ve la comanda hasta 5 s tarde | KDS hace *polling* cada 5 s, sin sonido ni timer | `frontend/src/hooks/use-kds-orders.ts:11` |
| Elegir producto = scrollear un dropdown de TODO el menú | Sin grilla, sin búsqueda, sin favoritos/más-vendidos | `frontend/src/features/orders/order-page.tsx:150-163` |
| Cantidad se tipea a mano | Sin botones +/− ni presets | `order-page.tsx` (input de cantidad) |
| No se ve el estado del salón | Lista de mesas sin estado (libre/ocupada/pidió cuenta) | `backend/app/domain/table/entities.py:7-16` |
| Se cae el wifi → se pierde la comanda | Cero offline / cola local / reintento | (no existe; `retry:false` global) |
| Caja sin atajos | Sin botones de monto rápido ni split de cuenta | `order-page.tsx:346-482` |
| Doble tap = doble ítem/pago | Mutaciones de orden sin idempotencia | `backend/app/presentation/api/v1/orders.py:91-144` |

**Lo bueno:** es **casi todo frontend + transporte**. El dominio (Clean Arch) está sano → **bajo riesgo arquitectónico**.

---

## Decisiones de arquitectura (propuestas — confirmar las marcadas ⚠️)
1. **IDs generados por el cliente + upsert idempotente** para los creates de alto riesgo (`OrderItem`, `Payment`, y
   `Order`). El cliente genera el `UUID` y lo manda; el server trata un repetido como **no-op idempotente** devolviendo
   el estado actual. Esto **habilita** optimistic UI (el ítem optimista usa el mismo id que persistirá → reconciliación
   trivial) **y** el reintento offline seguro. Es más simple que una tabla genérica de `idempotency_keys`.
2. **Realtime con SSE** (Server-Sent Events), **no WebSockets.** Unidireccional server→cliente alcanza para KDS y
   estado de mesas; SSE reusa HTTP, reconecta solo, y es más simple en FastAPI. **MVP: pub/sub in-process** (asyncio,
   por tenant). ⚠️ **Multi-instancia (Railway con >1 worker/replica) requiere un bus**: **Postgres `LISTEN/NOTIFY`**
   (preferido, ya tenemos PG) o Redis. Se deja el broadcaster detrás de un **port** para cambiar el backend sin tocar
   los endpoints.
3. **Auth del stream:** `EventSource` no manda header `Authorization`. → endpoint `GET /realtime/token` que devuelve un
   **JWT de stream de corta vida (~60 s)**; el cliente lo pasa como `?token=` en la URL del SSE. El server lo valida y
   **scopea el stream al `tenant_id`** del token (la aislación NO depende del LLM ni del cliente). Evita loguear el
   access token principal.
4. **Offline-first acotado al camino caliente del mozo:** se cachea el **catálogo de productos/mesas** y se **encola
   localmente** (IndexedDB) las mutaciones de comanda; al reconectar se **reproducen en orden** (seguras por la
   idempotencia de la decisión 1). ⚠️ **No** se hace offline de cobro/AFIP (requieren red por definición) — esos
   muestran estado "pendiente de conexión".
5. **Caja:** el split de cuenta se construye sobre el modelo de **pagos parciales que ya existe** (varios `Payment`
   por orden); se agrega UI de split (por ítem / por monto) y un helper de cálculo, sin cambiar el dominio de pagos.
6. **Sin cambios de dominio de negocio.** Se agrega `TableStatus` (derivado del estado de las órdenes; ver Tanda 2) y
   campos de soporte, pero la lógica de plata/órdenes/pagos no cambia. Todo sigue tenant-scoped + RLS.

## User Story
Como **mozo** quiero **armar y mandar una comanda en 3–4 toques y que aparezca al instante** (sin esperar al
servidor ni perderla si se corta el wifi); como **cocina** quiero **ver la comanda en <1 s con un sonido**; como
**cajero** quiero **cobrar en 2–3 toques con split de cuenta** — para que el sistema **se sienta más rápido** que el
que usan hoy y el local lo adopte sin fricción.

## Problem → Solution
Hoy cada acción bloquea en un round-trip, la cocina sondea cada 5 s, elegir un producto es scrollear, no se ve el
salón y un corte de red pierde la comanda. → **Optimistic UI + IDs idempotentes** (feedback 0 ms), **SSE** (cocina y
mesas en vivo), **grilla de productos con búsqueda/favoritos** (menos toques), **plano de salón con estados**,
**caja rápida con split**, y **cola offline** (confiabilidad). Resultado: captura a paridad/mejor, medida con métricas.

---

## Métricas norte (definición operativa de "rápido")
Instrumentar y comparar **antes/después** (Tanda 0 define la medición):

| Métrica | Hoy (aprox.) | Objetivo |
|---|---|---|
| Toques para mandar comanda de 3 ítems | ~15 | **≤ 7** |
| Tiempo "ítem en pantalla" tras el tap | 200–500 ms (spinner) | **~0 ms** (optimista) |
| Latencia KDS (enviar → visible en cocina) | hasta 5 s | **< 1 s** |
| Toques para cobrar (efectivo) | 4–5 | **≤ 3** |
| Comanda sobrevive corte de wifi | ❌ | **✅ (cola + reintento)** |

---

## Las 3 tandas (entregables independientes y mergeables)
- **🥇 Tanda 1 — "Se siente instantáneo"** (mayor impacto / menor esfuerzo): IDs idempotentes + batch, **optimistic
  UI**, **grilla de productos** (búsqueda/favoritos/+−), **KDS en SSE** (sonido + timer + color por demora).
- **🥈 Tanda 2 — Contexto operativo:** **plano de salón** con estados en vivo (SSE), comanda como **slide-over** sobre
  el plano, **caja rápida** (botones de medio de pago + montos preset + **split**).
- **🥉 Tanda 3 — Confiabilidad (offline):** **cola local** de comandas (IndexedDB) + reintento al reconectar +
  indicador de conexión + **PWA/service worker** para que la pantalla de comanda cargue sin red.

---

## Cambios transversales (backend)

### Idempotencia + batch (habilitador de Tanda 1 y 3)
- `POST /orders` acepta `id` (UUID del cliente) opcional → si ya existe (mismo tenant), **no-op** devolviendo la orden.
- `POST /orders/{id}/items` acepta `id` del ítem (UUID cliente) → repetido = no-op idempotente.
- **Nuevo** `POST /orders/{id}/items:batch` → agrega N ítems (+ opcional `send=true`) en **una transacción / un
  round-trip**. Permite "armar comanda entera y mandar" en un request.
- `POST /orders/{id}/payments` acepta `id` del pago (UUID cliente) → idempotente (hoy ya es "seguro por UUID" server-side).
- Mantener `_STATUS_BY_TYPE`: repetición no es error (200 con el estado actual), no 409.

### Realtime (SSE) — diseño
- **Port** `EventBus` (`publish(tenant_id, event)`, `subscribe(tenant_id) -> AsyncIterator[event]`). Adapter MVP
  **in-process** (asyncio `Queue` por tenant); adapter `PgNotifyEventBus` (LISTEN/NOTIFY) como camino de escala —
  ambos detrás del mismo port, cableados en `container.py` por `Selector(realtime_backend=memory|pg)`.
- **Emisión:** los use cases de orden (`SendOrder`, `AdvanceOrder`, `AddOrderItem`) publican un evento
  `{type, order_id, table_id, status}` tras persistir. (Inyectar el bus como port — no instanciar a mano.)
- **Endpoints:** `GET /realtime/token` (JWT 60 s, tenant-scoped) · `GET /kds/stream?token=…` ·
  `GET /floor/stream?token=…` (`StreamingResponse` / `sse-starlette`). El stream **filtra por tenant** del token.
- **GOTCHA:** heartbeat (`: keep-alive\n\n` cada ~15 s) para proxies; `Last-Event-ID` para reconexión; cerrar el
  generador al desconectar para no filtrar tareas.

### Estado de mesa (Tanda 2)
- `TableStatus` (StrEnum): `FREE / OCCUPIED / BILL_REQUESTED / PAYING`. **Derivado** del estado de las órdenes
  abiertas de la mesa (no duplicar verdad): FREE = sin orden abierta; OCCUPIED = orden OPEN/SENT/…; PAYING = pago
  parcial registrado; BILL_REQUESTED = flag opcional que setea el mozo. Endpoint `GET /floor` devuelve mesas +
  estado + total en vivo + `seated_since`. Cambios empujan por `floor/stream`.

### Config nueva
- `realtime_backend` (`memory|pg`, default `memory`), `realtime_token_ttl_s` (default 60),
  `realtime_heartbeat_s` (default 15). (Sin secretos nuevos; el JWT de stream firma con la misma key que el access token.)

---

## Mandatory Reading (moldes ya en el repo)
| Prio | File | Why |
|---|---|---|
| P0 | `frontend/src/hooks/use-orders.ts:32-54` | Mutaciones actuales (server-first) → acá va el `onMutate`/rollback optimista |
| P0 | `frontend/src/hooks/use-payments.ts:15-24` | Registrar pago server-first → optimista + idempotencia |
| P0 | `frontend/src/features/orders/order-page.tsx:150-163, 346-482` | Picker dropdown → grilla; sección cobro → caja rápida + split |
| P0 | `frontend/src/hooks/use-kds-orders.ts:11` | `refetchInterval:5000` → reemplazar por suscripción SSE |
| P0 | `frontend/src/features/kds/kds-page.tsx` | Board cocina → sonido, timer de antigüedad, color por demora |
| P0 | `frontend/src/features/floor/floor-page.tsx` | Grilla de mesas → plano con estados + slide-over |
| P0 | `backend/app/presentation/api/v1/orders.py:44-144` | Endpoints de orden → idempotencia + batch + emitir eventos |
| P0 | `backend/app/presentation/api/v1/payments.py:87` | Pago "seguro por UUID" → aceptar id del cliente |
| P0 | `backend/app/application/order/use_cases.py` | Use cases → inyectar `EventBus` y publicar tras persistir |
| P0 | `backend/app/infrastructure/persistence/database.py` | `set_config app.tenant_id` (RLS) → el runner del stream scopea por tenant |
| P0 | `backend/app/domain/table/entities.py:7-16` | `Table` (solo `active`) → agregar `TableStatus` derivado |
| P0 | `backend/app/container.py` | Wiring DI → cablear `EventBus` (Selector memory|pg) e inyectarlo en los use cases |
| P1 | `frontend/src/services/services-provider.tsx` + `services-context.ts` | DI de datos → agregar `realtimeApi` |
| P1 | `frontend/src/test/test-utils.tsx` | Registrar el nuevo servicio en el render de tests |

## External Documentation
| Topic | Source | Key Takeaway |
|---|---|---|
| Optimistic updates | tanstack.com/query (Optimistic Updates) | `onMutate` → `cancelQueries` + `setQueryData` (snapshot) ; `onError` rollback ; `onSettled` invalidate |
| SSE en FastAPI | `sse-starlette` / Starlette `StreamingResponse` | `EventSourceResponse(generator)`; heartbeat; `media_type=text/event-stream` |
| Postgres LISTEN/NOTIFY | postgresql.org | Bus pub/sub para multi-instancia sin Redis (escala del `EventBus`) |
| EventSource (browser) | MDN | No soporta headers → auth por query token; reconexión automática + `Last-Event-ID` |
| PWA offline / persisted mutations | tanstack.com/query (persistence) + Workbox | Cola de mutaciones + replay al reconectar; service worker para app-shell + catálogo |

---

## Files to Change

### Backend
| File | Action |
|---|---|
| `app/domain/realtime/ports.py` | CREATE — port `EventBus` + tipo `DomainEvent` |
| `app/infrastructure/realtime/{memory_bus,pg_notify_bus}.py` | CREATE — adapters in-process y LISTEN/NOTIFY |
| `app/presentation/api/v1/realtime.py` | CREATE — `GET /realtime/token`, `GET /kds/stream`, `GET /floor/stream` |
| `app/presentation/api/v1/orders.py` | UPDATE — aceptar `id` cliente (orden/ítem), endpoint `items:batch`, idempotencia |
| `app/presentation/api/v1/payments.py` | UPDATE — aceptar `id` cliente del pago (idempotente) |
| `app/presentation/api/v1/floor.py` | CREATE — `GET /floor` (mesas + estado derivado + total + seated_since) |
| `app/application/order/use_cases.py` | UPDATE — inyectar `EventBus`; publicar tras `add_item/send/advance`; `AddOrderItemsBatch` |
| `app/domain/table/entities.py` | UPDATE — `TableStatus` (derivado) + flag `bill_requested` |
| `app/container.py` | UPDATE — `Selector(realtime_backend)`; inyectar `EventBus` en use cases |
| `app/config.py` | UPDATE — `realtime_backend`, `realtime_token_ttl_s`, `realtime_heartbeat_s` |
| `pyproject.toml` | UPDATE — `sse-starlette` |
| `tests/unit/test_realtime_bus.py`, `tests/integration/test_e2e_realtime.py` | CREATE — pub/sub + stream tenant-scoped |
| `tests/integration/test_e2e_orders.py` | UPDATE — idempotencia (repetir add no duplica) + batch |

### Frontend
| File | Action |
|---|---|
| `src/api/realtime-api.ts` | CREATE — pide stream token + abre `EventSource` (cliente inyectable) |
| `src/api/{orders-api,payments-api}.ts` | UPDATE — enviar `id` cliente; `addItemsBatch` |
| `src/lib/ids.ts` | CREATE — `newId()` (uuid v4) para ítems/pagos/órdenes optimistas |
| `src/hooks/use-orders.ts` | UPDATE — `onMutate`/rollback optimista en add/send/advance; usar batch |
| `src/hooks/use-payments.ts` | UPDATE — pago optimista + idempotente |
| `src/hooks/use-kds-orders.ts` | UPDATE — reemplazar `refetchInterval` por suscripción SSE (fallback a poll) |
| `src/hooks/use-floor.ts` | CREATE — estado de mesas vía `GET /floor` + SSE |
| `src/features/orders/order-page.tsx` | UPDATE — grilla de productos (búsqueda + favoritos/más-vendidos), cantidad +/−, notas como chips, slide-over |
| `src/features/orders/product-grid.tsx` | CREATE — grilla tocable + búsqueda + "más vendidos primero" |
| `src/features/orders/quick-pay.tsx` | CREATE — botones de medio de pago + montos preset + split (por ítem / por monto) |
| `src/features/kds/kds-page.tsx` | UPDATE — SSE + sonido al entrar + timer de antigüedad + color por demora + bump 1 tap optimista |
| `src/features/floor/floor-page.tsx` | UPDATE — plano con estados en vivo (libre/ocupada/pidió cuenta/pagando) + total + tiempo sentado |
| `src/services/services-{context,provider}.tsx` | UPDATE — registrar `realtimeApi` |
| `src/lib/offline-queue.ts` (+ SW) | CREATE — cola IndexedDB de mutaciones + replay; service worker (Tanda 3) |
| `src/test/test-utils.tsx` | UPDATE — registrar `realtimeApi` fake |

---

## Step-by-Step Tasks

> Orden: **Tanda 0 (medición) → Tanda 1 → Tanda 2 → Tanda 3.** Validar (`ruff/mypy/pytest` · `tsc/eslint/vitest/build`)
> al cierre de cada tanda. Cada tanda es **commiteable/mergeable** por separado (`--no-ff`). La Tanda 1 ya entrega la
> mayor parte de la mejora percibida.

### Tanda 0 — Instrumentación / línea base
**T0** — Medir el "antes". `ACTION`: agregar marcas de performance (`performance.mark`/`measure`) en add-item→render,
send→KDS-visible, click-cobrar→confirmado; contador de toques en el flujo de comanda. Registrar la **línea base** de
las métricas norte en el reporte. `VALIDATE`: tabla antes/después arranca poblada con el "antes".

### Tanda 1 — "Se siente instantáneo"
**T1 — Backend: idempotencia + batch.** `ACTION`: `orders.py`/`payments.py` aceptan `id` del cliente; nuevo
`POST /orders/{id}/items:batch`. `IMPLEMENT`: repetido = no-op (200 con estado actual); batch en una transacción;
`AddOrderItemsBatch` use case. `MIRROR`: `orders.py:91-144`, use cases Fase 2. `GOTCHA`: idempotencia por
`(tenant_id, id)`; no romper el contrato actual (id opcional). `VALIDATE`: e2e "repetir add no duplica" + "batch agrega N + send".

**T2 — Frontend: optimistic UI.** `ACTION`: `use-orders.ts`/`use-payments.ts` con `onMutate`. `IMPLEMENT`: generar id
con `newId()`, `cancelQueries` + `setQueryData` (ítem/pago aparece YA), snapshot para rollback en `onError`,
`invalidate` en `onSettled`. El id optimista == id persistido → sin parpadeo. `MIRROR`: TanStack Optimistic Updates.
`GOTCHA`: deshabilitar el botón ya no es necesario; mostrar estado "sin confirmar" sutil, no spinner bloqueante.
`VALIDATE`: vitest del hook (item aparece antes de resolver; rollback ante error).

**T3 — Frontend: grilla de productos.** `ACTION`: `product-grid.tsx` reemplaza el dropdown. `IMPLEMENT`: grilla
tocable (targets grandes), **búsqueda as-you-type**, **favoritos / más-vendidos primero** (orden por popularidad —
reusar product performance de Fase 8 si está, o conteo local), cantidad con **+/−** (no tipear), nota como chips
rápidos. `MIRROR`: `order-page.tsx:150-163`, Cult UI (buscar componente de grilla/command antes de codear a mano).
`GOTCHA`: una mano, sin modales en el camino caliente. `VALIDATE`: build + recorrido manual (toques ≤ 7 para 3 ítems).

**T4 — KDS en tiempo real.** `ACTION`: backend `EventBus` + `GET /kds/stream`; front `use-kds-orders` por SSE.
`IMPLEMENT`: port `EventBus` + adapter memory; `SendOrder/AdvanceOrder` publican; `realtime-api` abre `EventSource`
con stream token; `kds-page` agrega **sonido** al entrar comanda, **timer de antigüedad**, **color por demora**, bump
de 1 tap optimista. Fallback a polling si el SSE no conecta. `MIRROR`: `database.py` (tenant scope), `kds-page.tsx`.
`GOTCHA`: heartbeat + cierre del generador; el stream filtra por tenant del token. `VALIDATE`: e2e — enviar en tenant
A llega al stream de A y **no** al de B; latencia < 1 s local.

### Tanda 2 — Contexto operativo
**T5 — Estado de mesa + endpoint floor.** `ACTION`: `TableStatus` derivado + `GET /floor` + `floor/stream`.
`IMPLEMENT`: estado a partir de órdenes abiertas/pagos; total en vivo + `seated_since`; empujar cambios por SSE.
`MIRROR`: `table/entities.py`, patrón SSE de T4. `VALIDATE`: floor refleja FREE→OCCUPIED→PAYING al operar una orden.

**T6 — Plano de salón + slide-over.** `ACTION`: `floor-page.tsx` con estados en vivo; comanda como **panel
deslizante** sobre el plano (no navegación de página). `IMPLEMENT`: color por estado, total y tiempo sentado por mesa,
tap = abre slide-over con la comanda (mantiene el contexto del salón). `MIRROR`: Cult UI (sheet/drawer). `VALIDATE`:
abrir/armar/cerrar comanda sin perder de vista el salón.

**T7 — Caja rápida + split.** `ACTION`: `quick-pay.tsx`. `IMPLEMENT`: botones de medio de pago, **montos preset**
(exacto, redondeo, billetes), **split por ítem / por monto** sobre pagos parciales existentes; cobrar en ≤ 3 toques.
`MIRROR`: `order-page.tsx:346-482`, `use-payments`. `GOTCHA`: el split reusa N `Payment` por orden (no cambia el
dominio). `VALIDATE`: cobrar mitad efectivo / mitad tarjeta deja la orden PAID con 2 pagos.

### Tanda 3 — Confiabilidad (offline)
**T8 — Cola offline + reintento.** `ACTION`: `offline-queue.ts` (IndexedDB) + indicador de conexión. `IMPLEMENT`:
encolar mutaciones de comanda cuando no hay red; **replay en orden** al reconectar (seguro por idempotencia T1);
banner "sin conexión / N cambios pendientes". `MIRROR`: TanStack persisted mutations. `GOTCHA`: NO encolar
cobro/AFIP (requieren red) → mostrar "pendiente de conexión". `VALIDATE`: cortar red → armar comanda → reconectar →
se sincroniza sin duplicar.

**T9 — PWA / service worker.** `ACTION`: SW para app-shell + cache del catálogo (productos/mesas). `IMPLEMENT`:
la pantalla de comanda **abre sin red** con el último catálogo; instalable en la tablet. `MIRROR`: Workbox/Vite PWA.
`VALIDATE`: en modo avión, `/app/floor` y la comanda cargan; al volver la red, sincroniza.

### Cierre
**T10 — Métricas + reporte.** Completar la tabla **antes/después**, escribir el reporte en
`.claude/PRPs/reports/fase-13-velocidad-operativa-report.md`, mover este plan a `plans/completed/`, actualizar PRD y
memoria.

---

## Validation Commands
### Backend
```bash
cd backend
poetry run ruff check . && poetry run mypy app
poetry run alembic upgrade head     # si hubo migración (TableStatus/flags): + downgrade -1 && upgrade head
poetry run pytest tests/unit tests/integration -q
```
EXPECT: ruff/mypy limpios; idempotencia + stream tenant-scoped en verde.

### Frontend
```bash
cd frontend
npx tsc --noEmit && npx eslint src && npx vitest run && npx vite build
```
EXPECT: cero errores; tests de optimismo/rollback y de SSE-fallback verdes.

### Manual / E2E local
- [ ] Armar comanda de 3 ítems en **≤ 7 toques**; el ítem aparece **al instante** (sin spinner).
- [ ] Cocina ve la comanda en **< 1 s** con **sonido**; bump en 1 tap.
- [ ] Plano de salón muestra estados en vivo; comanda en slide-over sin perder el salón.
- [ ] Cobrar en **≤ 3 toques**; split mitad/mitad deja la orden PAID.
- [ ] **Modo avión**: armar comanda → reconectar → sincroniza **sin duplicar**.

## Acceptance Criteria
- [ ] **Optimistic UI** en add-item/send/advance/pay (feedback ~0 ms; rollback ante error). Sin spinners bloqueantes.
- [ ] **Idempotencia** por id del cliente: repetir una mutación **no duplica** (probado en e2e).
- [ ] **KDS y mesas en tiempo real por SSE** (< 1 s), **tenant-scoped** (stream A nunca ve eventos de B). Fallback a poll.
- [ ] **Grilla de productos** con búsqueda + favoritos/más-vendidos + cantidad +/−; comanda en **≤ 7 toques**.
- [ ] **Plano de salón** con estados en vivo + slide-over; **caja rápida** con split (≤ 3 toques).
- [ ] **Cola offline** + reintento seguro + indicador; **PWA** abre la comanda sin red.
- [ ] Métricas norte medidas **antes/después** en el reporte. Backend/Front en verde. Multi-tenant + RLS intactos.

## Complexity / Confidence
- **Complejidad:** Alta (transversal: optimismo + realtime + offline), pero **bajo riesgo de dominio** (no cambia
  plata/órdenes/pagos). La parte fina es el **SSE multi-instancia** (mitigado con el port + LISTEN/NOTIFY) y el
  **offline** (mitigado por la idempotencia, que hace los replays seguros).
- **Confianza:** Alta en Tanda 1 (optimismo + idempotencia + SSE in-process son patrones conocidos y aislados).
  Media en Tanda 3 (offline/PWA — más superficie), por eso va última y es opt-in.

## Out of scope (diferido)
- Impresión térmica de comandas / ruteo a impresoras (otro gap del baseline competitivo, fase aparte).
- Multi-sucursal / consolidado; delivery (PedidosYa/Rappi); llamador de fila fast-food.
- WebSockets bidireccionales / colaboración multi-mozo en la misma comanda en vivo.
- Reportes + WhatsApp (Fase 10) y CRM (Fase 12) — esta fase los **precede** por prioridad de adopción.

## Risks
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| SSE no escala a >1 instancia en Railway | M | A | `EventBus` detrás de port; adapter `PgNotifyEventBus` (LISTEN/NOTIFY) listo como switch de config |
| Optimismo desincronizado con el server | M | M | id cliente == id persistido + idempotencia + `invalidate` en `onSettled`; snapshot/rollback en `onError` |
| Auth del stream filtra token en logs | B | M | JWT de stream dedicado de 60 s (no el access token); scope por tenant en el server |
| Offline duplica comandas al reconectar | M | A | Idempotencia (Tanda 1) **antes** que offline (Tanda 3); replay en orden con id estable |
| Alcance grande en una pasada | A | M | 3 tandas mergeables; Tanda 1 entrega el grueso; medir antes/después para frenar si ya alcanza |

## Notes
- **Estratégico:** esta fase **no es el diferenciador** — es el **peaje de entrada** que protege al asesor/copiloto.
  Llegar a *paridad o mejor* en captura es lo que habilita cobrar por la inteligencia.
- Es **casi todo frontend + transporte**: el dominio Clean Arch no se toca → bajo riesgo, alto retorno percibido.
- **Prioridad:** correr **antes de Fase 10 y 12**. Dentro de la fase, **Tanda 1 primero** (máximo "se siente" por menos código).
</content>
</invoke>
