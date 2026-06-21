# Plan: Fase 7 — Reservas + No-shows (Reservation)

## Summary
Gestionar **reservas** y **no-shows** sobre la Clean Arch + multi-tenant ya existentes. Modela `Reservation`
(cliente + cantidad de personas + fecha/hora + **turno** + mesa opcional) con un **ciclo de vida**
(PENDING → CONFIRMED → SEATED → COMPLETED, o CANCELLED / NO_SHOW). Provee una **agenda por día/turno/mesa**
(vista del servicio), confirmaciones y marcado de **no-show**. Genera la fuente de dato para el futuro KPI de
no-shows (Capa 2 / Fase 9). Prioridad PRD: *Could*. Más relevante para hotel, pero el MVP arranca **restaurante**
(reserva de mesa por turno).

> **DECISIONES DE ALCANCE (cerradas — no re-litigar):**
> 1. **Restaurante primero.** Reserva = cliente + N personas + fecha/hora + **turno** (ALMUERZO/CENA) + **mesa
>    opcional**. Hotel (reserva→folio→cobro, channel manager) **diferido** — es otro modelo, no este.
> 2. **Mesa opcional.** Una reserva puede quedar **sin mesa asignada** (se asigna al sentar / a mano). Si se
>    asigna, la mesa debe existir (`TableRepository`, reusa `TableNotFound`).
> 3. **La reserva NO bloquea por capacidad/solape.** No se valida disponibilidad ni overbooking (igual criterio que
>    "la venta no se frena por stock"): la agenda es informativa; doble reserva de mesa/turno **no se rechaza**
>    (las mesas rotan). Guard de solape = **diferido**.
> 4. **Ciclo de vida explícito** con transiciones validadas (estilo `Order`): `confirm`, `seat`, `complete`,
>    `cancel`, `mark_no_show`. Estados terminales (COMPLETED/CANCELLED/NO_SHOW) no transicionan.
> 5. **Confirmaciones = cambio de estado manual** por el personal (PENDING→CONFIRMED). **Sin WhatsApp/recordatorios
>    automáticos** (lo toma Fase 10). No-show = marcado **manual** (no automático por hora).
> 6. **Sin enganche a `Order`.** Sentar una reserva **no** crea ni linkea comanda en el MVP (link reserva↔comanda
>    diferido). El ciclo de la reserva es autónomo.
> 7. **Turno** = `ServiceTurn` (StrEnum ALMUERZO/CENA) seteado por el usuario; la agenda agrupa por día + turno.
>    Timestamps de servidor para `created_at`; `reserved_at` lo provee el cliente (la fecha/hora deseada).
> 8. **Multi-tenant + RLS** en todo; código 100% inglés, UX español, errores `{code EN, message ES}`.

## Estado de implementación
PENDIENTE. Depende de Fase 1 (identidad/RBAC) y Fase 2 (`Table`) — ✅ ambas en `main`. Se implementa en rama
`feat/fase-7-reservas-noshows`. Roadmap: tras Reservas, Fase 8 (modelo canónico) puede consumir no-shows.

## User Story
Como **anfitrión/encargado** quiero **cargar reservas, verlas en una agenda por turno y mesa, confirmarlas y
marcar no-shows** para **organizar el servicio y no perder mesas** sin cuaderno ni WhatsApp suelto.

## Problem → Solution
Hoy las reservas viven en un cuaderno o en WhatsApp, sin visión del servicio ni registro de no-shows. →
`Reservation` con ciclo de vida + una **agenda** filtrable por día/turno; confirmaciones y no-shows quedan
registrados (fuente para el KPI de no-shows del asesor). Todo scoped por `tenant_id` + RLS.

---

## Modelo de dominio (nuevo: `reservation`)
- **`Reservation`** (entidad): `id, tenant_id, customer_name, customer_phone|None, party_size (int>0),
  reserved_at (datetime), turn (ServiceTurn), table_id|None, status (ReservationStatus), note|None, created_at`.
  Métodos (transiciones, estilo `Order._advance`):
  - `confirm()`: PENDING → CONFIRMED.
  - `seat()`: PENDING|CONFIRMED → SEATED.
  - `complete()`: SEATED → COMPLETED.
  - `cancel()`: PENDING|CONFIRMED → CANCELLED.
  - `mark_no_show()`: PENDING|CONFIRMED → NO_SHOW.
  - `reschedule(*, reserved_at, turn, party_size, table_id)`: edita datos mientras no esté en estado terminal.
  - Estados terminales (COMPLETED/CANCELLED/NO_SHOW) → cualquier transición lanza `InvalidReservationTransition`.
- **VOs:**
  - `ReservationStatus` (StrEnum): `PENDING, CONFIRMED, SEATED, COMPLETED, CANCELLED, NO_SHOW`.
  - `ServiceTurn` (StrEnum): `LUNCH, DINNER` (UX: "Almuerzo"/"Cena").
- **Excepciones:** `ReservationNotFound`, `InvalidReservationTransition`, `InvalidPartySize` (todas con `code` EN +
  `message` ES). Reusa `TableNotFound` (Fase 2) al asignar mesa.
- **Ports:** `ReservationRepository` (`get_by_id`, `list` con filtros `since/until/turn/status/table_id`, `add`,
  `save`). Scoped por `tenant_id` (defensa en profundidad sobre RLS).

## Read model / Agenda
- **Agenda = `ListReservations`** con filtros (día via `since/until`, `turn`, `status`). El frontend agrupa por
  turno y ordena por `reserved_at`. **No** hace falta un read model dedicado para el MVP (la lista alcanza); un
  `ReservationAgendaReadModel` con conteos por estado queda **diferido** a Fase 8/9.

## Config
- (Opcional) horarios por turno por tenant — **diferido**; el turno lo elige el usuario al cargar la reserva.

---

## Mandatory Reading (moldes ya en el repo)
- **Fase 2 (catálogo/mesas, molde de CRUD simple + ciclo de vida):** `domain/table/{entities,repository,exceptions}.py`,
  `domain/order/entities.py` (transiciones `_advance` + guards), `domain/order/value_objects.py` (StrEnum de estado),
  `application/table/use_cases.py`, `presentation/api/v1/tables.py`, `presentation/schemas/tables.py`.
- **Fase 6 (molde end-to-end recién hecho):** `domain/inventory/*`, `application/inventory/use_cases.py`,
  `infrastructure/persistence/{ingredient_repo,recipe_repo}.py`, `presentation/api/v1/inventory.py`,
  `presentation/schemas/inventory.py`, `alembic/versions/0008_inventory.py` (create + GRANT + ENABLE/FORCE RLS +
  policy `tenant_isolation`), edición de `models.py`/`mappers.py`/`container.py`/`errors.py`/`main.py`/
  `tests/integration/conftest.py` (`_TABLES`).
- **DI + RBAC + errores + router:** `container.py`, `presentation/rbac.py`, `presentation/deps.py` (`current_identity`),
  `presentation/errors.py`, `main.py`.
- **Frontend:** `api/inventory-api.ts` + `hooks/use-inventory.ts` + `features/inventory/stock-page.tsx`
  (tabla + sheet de alta + acciones por fila), `features/timeclock/staff-page.tsx` (filtro por fecha),
  `components/shell/nav-config.ts`, `app/router.tsx`, `services/services-{context,provider}`, `test/test-utils.tsx`,
  `lib/inventory.ts` (labels + formato).

## Files to Change (orientativo)
**Backend (nuevos):** `domain/reservation/{__init__,entities,value_objects,exceptions,repository}.py`,
`application/reservation/{__init__,use_cases}.py`, `infrastructure/persistence/reservation_repo.py`,
`presentation/api/v1/reservations.py`, `presentation/schemas/reservations.py`,
`alembic/versions/0009_reservations.py`, tests unit + e2e.
**Backend (editar):** `models.py`, `mappers.py`, `container.py`, `presentation/errors.py`, `main.py`,
`tests/integration/conftest.py` (`_TABLES` ← prepend `reservations`).
**Frontend (nuevos):** `api/types-reservations.ts`, `api/reservations-api.ts` (+ `.test.ts`),
`hooks/use-reservations.ts`, `lib/reservations.ts` (+ `.test.ts`), `features/reservations/reservations-page.tsx`.
**Frontend (editar):** `services/services-{context,provider}`, `test/test-utils.tsx`,
`components/shell/nav-config.ts` (grupo "Operación" → "Reservas"), `app/router.tsx`.

---

## Step-by-Step Tasks

### T1 — Dominio reservation
- `Reservation` (transiciones con guards), VOs (`ReservationStatus`, `ServiceTurn`), excepciones, port
  `ReservationRepository`.
- **Tests unit:** cada transición válida; transición inválida (terminal → cualquiera) lanza
  `InvalidReservationTransition`; `party_size ≤ 0` lanza `InvalidPartySize`; `reschedule` actualiza datos y rechaza
  en estado terminal.
- **MIRROR:** `domain/order/entities.py` (`_advance`/guards), `domain/order/value_objects.py`,
  `domain/inventory/{exceptions,repository}.py`.

### T2 — Persistencia + migración RLS
- ORM `reservations` + mapper + repo `SqlAlchemyReservationRepository` (`list` con filtros `since/until/turn/status/
  table_id`, ordena por `reserved_at`). **Migración `0009_reservations`** (down_revision `0008_inventory`): create +
  GRANT + ENABLE/FORCE RLS + policy `tenant_isolation`. `conftest._TABLES` ← prepend `reservations`.
- **MIRROR:** `alembic/versions/0008_inventory.py`, `models.py` (TableORM/ShiftORM), `mappers.py`,
  `infrastructure/persistence/{ingredient_repo,shift_repo}.py`.

### T3 — Use cases + API + RBAC
- Use cases: `CreateReservation` (valida `party_size` y, si hay mesa, `TableNotFound`), `ListReservations`
  (agenda con filtros), `GetReservation`, `ConfirmReservation`, `SeatReservation`, `CompleteReservation`,
  `CancelReservation`, `MarkNoShow`, `UpdateReservation` (reschedule/reassign). Router `/reservations/*`
  (OWNER/MANAGER/WAITER/CASHIER — front of house). Container + `errors.py`
  (`ReservationNotFound`=404, `InvalidReservationTransition`=409, `InvalidPartySize`=422) + `main.py`.
- **Tests e2e:** alta → confirmar → sentar → completar; alta → no-show; transición inválida (409); mesa inexistente
  (404); agenda filtra por día/turno; RLS aislada entre tenants.
- **MIRROR:** `application/inventory/use_cases.py`, `application/table/use_cases.py`,
  `presentation/api/v1/{inventory,tables}.py`, `rbac.py`.

### T4 — Frontend
- `ReservationsApi` + `use-reservations` hooks; registrar en `services-{context,provider}` + `test-utils`.
- `lib/reservations.ts`: `RESERVATION_STATUS_LABELS`, `SERVICE_TURN_LABELS`, formato de fecha/hora.
- Página **Reservas** (`/app/reservations`): selector de **día** + filtro de **turno**, lista/tabla agrupada por
  turno con badges de estado y acciones por fila (Confirmar / Sentar / Completar / Cancelar / No-show), sheet
  **Nueva reserva** (cliente, teléfono, personas, fecha+hora, turno, mesa opcional). Nav grupo "Operación" →
  "Reservas" (roles front of house) + ruta.
- **Validar:** tsc + eslint + vitest + build.
- **MIRROR:** `features/inventory/stock-page.tsx`, `features/timeclock/staff-page.tsx`,
  `hooks/use-inventory.ts`, `api/inventory-api.ts`, `lib/inventory.ts`.

---

## Validation Commands
- **Backend:** `poetry run ruff check app tests` · `poetry run mypy app` · `poetry run pytest -q` (cobertura ≥ 80%
  en domain/application).
- **Frontend:** `npx tsc --noEmit` · `npx eslint src` · `npx vitest run` · `npx vite build`.

## Acceptance Criteria
- Crear una reserva (con o sin mesa); **confirmar**, **sentar**, **completar**; alternativamente **marcar no-show**.
- Transición inválida (p. ej. completar una reserva ya cancelada) se rechaza con `code` estable (409).
- Asignar una mesa inexistente devuelve `table_not_found` (404).
- **Agenda** filtra por día y turno y muestra el estado de cada reserva (visible en el servicio).
- Scoped por tenant (RLS). ruff + mypy + pytest + tsc + eslint + vitest + build en verde.

## Complexity / Confidence
- **Complejidad:** Baja-media. Es CRUD + máquina de estados sobre patrones ya probados (Order para transiciones,
  Inventory/Table como molde end-to-end). Sin cross-aggregate (a diferencia de Fase 6 T4). 4 tramos.
- **Confianza:** Alta en los 4 tramos (todo tiene molde directo en el repo).

## Out of scope (diferido)
- Enganche reserva↔comanda (crear/linkear `Order` al sentar); guard de solape/capacidad/overbooking; recordatorios
  y confirmaciones por WhatsApp/email (Fase 10); no-show automático por hora; depósito/seña por reserva (anti
  no-show); waitlist; reservas online del comensal (portal público); modelo hotelero (reserva→folio→cobro, channel
  manager); KPI de no-shows como métrica del asesor (Fase 9) y read model de agenda con conteos (Fase 8).
