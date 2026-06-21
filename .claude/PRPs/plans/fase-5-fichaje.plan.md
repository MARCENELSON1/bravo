# Plan: Fase 5 — Fichaje (Shift) + reporte por mozo

## Summary
Registrar **horas trabajadas** del personal (`Shift` entrada→salida) y **atribuir mesas/ventas por mozo** cruzando con la comanda, sobre la Clean Arch + multi-tenant ya existentes. Habilita el **labor cost** real para la Capa 2 (asesor) y un **reporte por mozo** (horas, extras, mesas, ventas). El fichaje es **proof-of-presence opcional vía QR/código rotativo** encima del flujo base, detrás de un port `PresenceToken` (reversible / desactivable). No introduce identidad nueva: **el empleado es el `User` logueado**.

> **DECISIÓN DE ALCANCE (cerrada con el usuario):**
> 1. **Identidad = Usuario logueado.** `Shift.user_id` referencia al `User`. Cada uno **se ficha desde su sesión** (auto-fichaje). El kiosko/PIN para personal sin login queda **diferido**.
> 2. **Flujo = toggle.** Un solo botón que alterna según el estado: si no hay turno abierto → **entrada** (crea `Shift` OPEN); si hay uno abierto → **salida** (lo cierra). **Varios `Shift` por día** son válidos (turno cortado / pausa = salida+entrada). El día = suma de los `Shift` cerrados.
> 3. **Extras = umbral de jornada configurable, sobre el TOTAL del día.** `standard_workday_minutes` por tenant (default **480 = 8 h**). `overtime = max(0, total_del_día − umbral)` — **nunca por turno** (un turno cortado 5+5 no daría extras por tramo pero sí sobre el día).
> 4. **Timestamps de servidor** (nunca del cliente), mismo criterio anti-fraude que AFIP/pagos.
> 5. **Correcciones del encargado con auditoría** (olvido de salida, etc.): OWNER/MANAGER editan entrada/salida y queda registrado quién/cuándo (`adjusted_by`, `source=MANAGER`). **Auto-cierre a fin de día diferido.**
> 6. **Capa de presencia (QR + código), incremental (Fase 5.5 / tramo T6):** una pantalla en el local muestra un **QR + código corto** que **rota por tiempo** (estilo TOTP, TTL ≤ 60 s, firmado). El empleado **escanea o tipea** desde su app; el backend valida el token (firma + no vencido + del tenant + **single-use por (token, user)** + **rate-limit**) y recién ahí registra el fichaje del **usuario logueado**. El token es **prueba de presencia, no identidad**. La pantalla obtiene el token con una **credencial de dispositivo** (no una sesión de empleado), para que el QR **no se pueda obtener de forma remota**. **Breaks explícitos (botón Pausa) diferidos** (hoy una pausa = salida+entrada).

## Estado de implementación
PENDIENTE. Depende de Fase 2 (comandas, `Order.waiter_id`) y se cruza con Fase 3 (ventas) — ✅ ambas en `main`. Se implementa en rama `feat/fase-5-fichaje`. Roadmap: tras Fichaje, Fase 6 (Stock/Food-cost). Prioridad PRD: *Should* (habilita labor cost para el asesor).

## User Story
Como **empleado (cualquier rol operativo)** quiero **fichar mi entrada y salida en un toque** para que **mis horas queden registradas sin planillas**. Como **dueño/encargado (OWNER/MANAGER)** quiero **ver horas, extras, mesas y ventas por mozo en un período** para **decidir turnos y entender el costo de personal**.

## Problem → Solution
Hoy no hay registro de horas ni atribución formal por mozo. → Sobre el `User` logueado, un **toggle** abre/cierra `Shift` (timestamps de servidor). Las horas del período salen de sumar los `Shift`; las **extras** se calculan sobre el total diario vs el umbral del tenant; **mesas/ventas por mozo** se derivan de `Order.waiter_id` (+ totales de Fase 3) en un **read model** dedicado. El **QR/código rotativo** (capa opcional) prueba presencia física sin cambiar el modelo de `Shift`: valida el token y delega en los mismos `ClockIn/ClockOut`.

---

## Modelo de dominio (nuevo: `timeclock`)
- **`Shift`** (agregado): `id, tenant_id, user_id, clock_in_at: datetime, clock_out_at: datetime|None, status (ShiftStatus), source (ShiftSource), note|None, adjusted_by: str|None, created_at`. Métodos: `close(at: datetime)` (invariante: no cerrar si ya CLOSED; `at >= clock_in_at`), `adjust(*, clock_in_at, clock_out_at, by)`. Propiedad `worked_minutes -> int | None` (None si OPEN).
- **VOs:**
  - `ShiftStatus` (StrEnum): `OPEN → CLOSED`.
  - `ShiftSource` (StrEnum): `SELF` (toggle desde sesión), `PRESENCE` (QR/código), `MANAGER` (corrección). Para auditoría.
- **Funciones puras (testeables, estilo `taxation.py`):**
  - `total_worked_minutes(shifts: list[Shift]) -> int` (ignora abiertos o los cuenta hasta `now`, a decidir; para el reporte, sólo cerrados).
  - `daily_overtime(minutes_in_day: int, standard_workday_minutes: int) -> int = max(0, minutes_in_day - standard)`. El agrupado por día se hace en el read model / use case; la función es pura.
- **Excepciones:** `ShiftAlreadyOpen` (`shift_already_open`), `NoOpenShift` (`no_open_shift`), `ShiftNotFound` (`shift_not_found`). (+ presencia: `InvalidPresenceToken`, `PresenceTokenReused`, `PresenceRateLimited`.)
- **`ShiftRepository`** (port): `get_open_for_user(tenant_id, user_id)`, `get_by_id`, `list(tenant_id, *, user_id=None, since=None, until=None)`, `add`, `save`.

## Config (Tenant)
- Agregar **`standard_workday_minutes: int = 480`** a `Tenant` (dominio + ORM + migración). Es el umbral de jornada para las extras. (Patrón: `Tenant` ya ganó `country/currency` en Fase 2.)

## Capa de presencia (T6 — opcional/incremental)
- **`PresenceToken`** (port): `current(tenant_id, device_id) -> PresenceChallenge{qr_payload, code, expires_at}` (lo consume la pantalla) y `verify(tenant_id, presented: str, user_id) -> None` (valida firma + ventana de tiempo + **single-use por (token, user)** + **rate-limit**; eleva las excepciones de presencia).
- **`HmacPresenceToken`** (adapter): token = firma `HMAC(secret, f"{tenant_id}:{device_id}:{time_step}")`; `time_step = floor(now / period)`, period ≤ 60 s; `verify` acepta el paso actual y el anterior (skew/concurrencia). `code` = derivación corta legible (ej. base32 de 6–8 chars) del mismo token; `qr_payload` = token completo. Single-use: tabla/almacén `used_presence_tokens(tenant_id, time_step, user_id)` con TTL corto. Rate-limit por `user_id` (X intentos/min).
- **Credencial de dispositivo:** la pantalla del local se autentica con un **device token** provisto por el OWNER (flujo "registrar dispositivo de fichaje", **molde = conectar integración**), distinto de las sesiones de empleado → el QR rotativo **no se obtiene remoto**.
- **Secreto de firma:** dedicado por tenant (o derivado del `jwt_secret`, molde = `state_secret` de `StartMercadoPagoConnection`).
- **Integración con el fichaje:** `ClockIn/ClockOut` siguen igual; un endpoint `POST /timeclock/punch` recibe `{presented}`, llama `PresenceToken.verify(...)` y delega en el toggle con `source=PRESENCE`. El toggle base (`source=SELF`) sigue disponible (honor-system / equipos chicos / fallback).

## Reporte por mozo (read model)
- **`StaffReportReadModel`** (molde = `SqlAlchemyDashboardReadModel`): por `user_id` y período devuelve `worked_minutes`, `overtime_minutes` (sumando `daily_overtime` por día vs el umbral del tenant), `tables_served` (count distinct `Order.table_id` con `waiter_id=user`), `sales_amount` (Σ totales de comandas `PAID` del mozo, en `Money`). Scoped por `tenant_id` + RLS.

## Ports & Adapters
- `ShiftRepository` → `SqlAlchemyShiftRepository`.
- `StaffReportReadModel` → `SqlAlchemyStaffReportReadModel`.
- `PresenceToken` → `HmacPresenceToken` (+ `NoPresence`/passthrough para desactivarlo por config, estilo Selector `email_sender`/`payment_gateway`/`invoicing_provider`).
- DI por constructor en `container.py`; overrides con fakes en tests.

---

## Mandatory Reading (moldes ya en el repo)
- **Fase 3 (pagos):** `domain/payment/{entities,ports}.py`, `application/payment/use_cases.py`, `presentation/api/v1/payments.py`, container Selector → molde de entidad + port + use case + API + RBAC.
- **Reporting (read model):** `application/reporting/dashboard.py` + `infrastructure/persistence/dashboard_repo.py` (`SqlAlchemyDashboardReadModel`) → molde directo del **reporte por mozo**.
- **Order (atribución):** `domain/order/{entities,repository}.py` (`waiter_id`, `table_id`, `total()`, estado `PAID`).
- **Tenant (config):** `domain/identity/...` + `Tenant` ORM (agregar `standard_workday_minutes`).
- **Persistencia/migración RLS:** `0003_payments.py` / `0005_invoices.py` (ENABLE/FORCE RLS + policy `tenant_isolation`), `models.py`, `mappers.py`.
- **Token firmado corto:** `application/payment/connect_mercadopago.py` (`StartMercadoPagoConnection` firma el `state` con TTL) → molde del `PresenceToken`.
- **Frontend:** `api/payments-api.ts` + `hooks/use-payments.ts` (cliente inyectable + hooks), `features/orders/order-page.tsx` (widget de acción), `features/expenses/expenses-page.tsx` (tabla + período), `components/shell/{app-shell,nav-config}.tsx/ts`, `app/router.tsx`, `services/services-{context,provider}`, `api/reports-api.ts` + `hooks/use-dashboard.ts`.

## Files to Change (orientativo)
**Backend (nuevos):** `domain/timeclock/{entities,value_objects,exceptions,repository,presence}.py`, `domain/timeclock/hours.py` (puro), `application/timeclock/use_cases.py`, `application/timeclock/presence.py`, `infrastructure/persistence/{shift_repo,staff_report_repo}.py`, `infrastructure/timeclock/hmac_presence.py`, `presentation/api/v1/timeclock.py`, `presentation/schemas/timeclock.py`, `alembic/versions/0006_shifts.py`, tests unit + e2e.
**Backend (editar):** `models.py`, `mappers.py`, `container.py`, `config.py` (`presence_provider`, `standard_workday_default`, period/secret), `presentation/errors.py` (mapear excepciones), `main.py` (router), `Tenant` (dominio+ORM), `tests/integration/conftest.py` (`_TABLES`).
**Frontend (nuevos):** `api/timeclock-api.ts`, `api/types-timeclock.ts`, `hooks/use-timeclock.ts`, `features/timeclock/staff-page.tsx`, `features/timeclock/presence-display-page.tsx` (T6), `components/shell/clock-toggle.tsx` (widget).
**Frontend (editar):** `components/shell/app-shell.tsx` (widget en topbar), `components/shell/nav-config.ts` (nav "Personal"), `app/router.tsx`, `services/services-{context,provider}`, `test/test-utils.tsx`.

---

## Step-by-Step Tasks

### T1 — Dominio timeclock
- `Shift` + `ShiftStatus` + `ShiftSource`; `hours.py` (`total_worked_minutes`, `daily_overtime`); excepciones; `ShiftRepository` port.
- **Tests unit:** toggle (open→close), no cerrar dos veces, `daily_overtime` (8h→0, 8.5h→0.5, turno cortado 5+5→2), `worked_minutes`.
- **MIRROR:** `domain/payment/entities.py`, `domain/invoice/taxation.py`.

### T2 — Persistencia + config Tenant
- `ShiftORM` (tabla `shifts`: id, tenant_id FK, user_id FK, clock_in_at, clock_out_at|None, status index, source, note|None, adjusted_by|None, created_at) + mapper + `SqlAlchemyShiftRepository`.
- `standard_workday_minutes` en `Tenant` (dominio + ORM).
- **Migración `0006_shifts`** (down_revision `0005_invoices`): create tabla + GRANT + ENABLE/FORCE RLS + policy `tenant_isolation`; `ALTER tenants ADD standard_workday_minutes`.
- `conftest._TABLES` ← prepend `"shifts"`.
- **MIRROR:** `0005_invoices.py`, `infrastructure/persistence/{invoice_repo,mappers,models}.py`.

### T3 — Casos de uso + API base + RBAC
- `ClockIn` (rechaza si hay open → `ShiftAlreadyOpen`), `ClockOut` (rechaza si no hay open → `NoOpenShift`), `Punch` (toggle: abre o cierra según estado), `GetMyTimeclock` (turno abierto + recientes), `ListShifts` (manager: por empleado/período), `AdjustShift` (corrección con `adjusted_by`, `source=MANAGER`).
- Router `/timeclock`: `POST /punch` (o `/clock-in`+`/clock-out`), `GET /me`, `GET /shifts` (OWNER/MANAGER), `PATCH /shifts/{id}` (OWNER/MANAGER). RBAC: roles operativos fichan; OWNER/MANAGER listan/corrigen. Container wiring; `errors.py`.
- **Tests e2e:** entrada→salida→listado; doble entrada → 409 `shift_already_open`; salida sin abrir → 409 `no_open_shift`; corrección por manager.
- **MIRROR:** `application/payment/use_cases.py`, `presentation/api/v1/payments.py`, `rbac.py`.

### T4 — Read model + reporte por mozo
- `StaffReportReadModel` (join `shifts` + `orders.waiter_id` + totales) → horas, extras (Σ `daily_overtime` por día vs umbral del tenant), mesas, ventas por empleado/período. `GetStaffReport` use case. `GET /reports/staff?from&to`.
- **Tests e2e:** mozo con turnos + comandas PAID → reporte con horas/extras/mesas/ventas correctos.
- **MIRROR:** `application/reporting/dashboard.py`, `infrastructure/persistence/dashboard_repo.py`.

### T5 — Frontend base
- `TimeClockApi` inyectable + `use-timeclock` hooks (TanStack); registrar en `services-{context,provider}` + `test-utils`.
- **Widget `clock-toggle`** en el topbar del `AppShell`: muestra estado (Fichar entrada / Fichar salida) + cronómetro del turno en curso; toast de confirmación.
- Página **Personal** (OWNER/MANAGER): tabla de fichajes por empleado + filtro de período + totales (horas, extras) + corrección (sheet). **Reporte por mozo** (horas/extras/mesas/ventas). Nav "Personal" + ruta `/app/staff`.
- **Validar:** tsc + eslint + vitest + build.
- **MIRROR:** `hooks/use-payments.ts`, `features/expenses/expenses-page.tsx`, `features/orders/order-page.tsx`, `hooks/use-dashboard.ts`.

### T6 — Capa de presencia (QR + código) — Fase 5.5 incremental
- `PresenceToken` port + `HmacPresenceToken` adapter (rotación por tiempo, ventana actual+anterior, single-use por (token,user), rate-limit) + tabla/almacén de single-use. Selector `presence_provider` (hmac|off).
- **Credencial de dispositivo** por local (provisión por OWNER; molde = conectar integración). Endpoint `GET /timeclock/presence/current` (auth de dispositivo) para la pantalla.
- `POST /timeclock/punch` acepta `{presented}` → `verify` → toggle con `source=PRESENCE`.
- **Pantalla de fichaje** (display): muestra QR + código rotando. **App:** scanner (cámara) + input para tipear el código.
- **Tests:** token válido/vencido, paso anterior aceptado, replay rechazado (`presence_token_reused`), rate-limit, código tipeable equivale al QR.
- **MIRROR:** `connect_mercadopago.py` (firma+TTL), Selector del container, flujo de integraciones (provisión).

---

## Validation Commands
- **Backend:** `poetry run ruff check app tests` · `poetry run mypy app` · `poetry run pytest -q` (cobertura ≥ 80% en domain/application).
- **Frontend:** `npx tsc --noEmit` · `npx eslint src` · `npx vitest run` · `npx vite build`.

## Acceptance Criteria
- Un empleado ficha entrada y salida (toggle) desde su sesión; **varios turnos/día** suman bien; timestamps de servidor.
- Doble entrada y salida-sin-abrir se rechazan con `code` estable.
- OWNER/MANAGER ven fichajes por empleado/período y **corrigen** con auditoría.
- **Reporte por mozo** muestra horas, **extras (diario vs umbral)**, mesas y ventas, scoped por tenant (RLS).
- (T6) El QR/código **rota por tiempo**, es **single-use**, rate-limited, y sólo obtenible con credencial de dispositivo; escanear **o** tipear registra el fichaje del usuario logueado.
- ruff + mypy + pytest + tsc + eslint + vitest + build en verde.

## Complexity / Confidence
- **Complejidad:** Media. T1–T5 son CRUD+read model sobre patrones ya probados (alto reuso). T6 (presencia) es la parte novedosa (token rotativo + device credential + pantalla + scanner) → media-alta, por eso va **incremental y aislada detrás de un port**.
- **Confianza:** Alta en T1–T5 (moldes directos de Fases 2/3 + reporting). Media en T6 (UX de cámara + provisión de dispositivo; el dominio no se toca).

## Out of scope (diferido)
- Kiosko/PIN para personal sin login; auto-cierre de turnos olvidados; **botón Pausa** explícito (break que descuenta sin cerrar); límites **semanales** de horas extra (hoy sólo umbral diario); geofencing/atadura a dispositivo más allá de la credencial; export a liquidación de sueldos (lo toma la Capa 2 / Fase 8 canónica).
