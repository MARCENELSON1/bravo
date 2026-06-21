# Implementation Report: Fase 5 — Fichaje (Shift) + reporte por mozo

## Summary
Core del fichaje implementado de punta a punta (T1–T5): cada empleado **es el
`User` logueado** y ficha entrada/salida con un **toggle** desde su sesión;
varios turnos por día suman bien; las **extras** se calculan sobre el total
diario vs un umbral por tenant (`standard_workday_minutes`, default 480);
OWNER/MANAGER **listan y corrigen** fichajes con auditoría (`adjusted_by`,
`source=MANAGER`); y un **reporte por mozo** cruza horas/extras con
mesas/ventas (`Order.waiter_id` + comandas PAID) en un read model dedicado.
Todo sobre la Clean Arch + multi-tenant + RLS ya existentes. Timestamps **de
servidor** (anti-fraude). **T6 (capa de presencia QR/código) queda diferido**
como Fase 5.5 — ver "Out of scope / Próximo".

## Assessment vs Reality

| Metric | Predicted (Plan) | Actual |
|---|---|---|
| Complejidad | Media (T1–T5) / media-alta (T6) | Media — sin sorpresas, alto reuso de moldes |
| Confianza | Alta T1–T5 | Confirmada: todo verde a la primera tras lint/types |
| Tramos | T1–T6 | **T1–T5 completos**; T6 diferido (Fase 5.5) |

## Tasks Completed

| # | Task | Status | Notes |
|---|---|---|---|
| T1 | Dominio `timeclock` | ✅ Complete | `Shift` (close/adjust/worked_minutes), `hours.py` puro, excepciones, port |
| T2 | Persistencia + config Tenant | ✅ Complete | `ShiftORM`, mappers, repo, migración `0006_shifts` (RLS), `standard_workday_minutes` |
| T3 | Casos de uso + API + RBAC | ✅ Complete | ClockIn/ClockOut/Punch/GetMyTimeclock/ListShifts/AdjustShift + router `/timeclock` |
| T4 | Read model + reporte por mozo | ✅ Complete | `StaffReportReadModel` + `GET /reports/staff` (OWNER/MANAGER) |
| T5 | Frontend base | ✅ Complete | `TimeClockApi` + hooks, widget `ClockToggle` en topbar, página **Personal**, nav + ruta |
| T6 | Capa de presencia (QR + código) | ⏸️ Diferido | Fase 5.5 — el plan lo define incremental y aislado detrás de `PresenceToken` |

## Validation Results

| Level | Status | Notes |
|---|---|---|
| Static Analysis | ✅ Pass | `ruff check app tests` + `mypy app` (170 files) limpios; `tsc` + `eslint src` limpios |
| Unit Tests | ✅ Pass | Backend 10 unit (timeclock domain) + frontend 9 (api+lib) nuevos |
| Build | ✅ Pass | `vite build` OK |
| Integration | ✅ Pass | Backend **127 tests** (e2e fichaje 7 + e2e staff report 2 nuevos, RLS incluido) |
| Coverage | ✅ Pass | domain/application nuevos 94–100% (≥80% exigido) |

## Files Changed

### Backend — nuevos
| File | Action |
|---|---|
| `app/domain/timeclock/{__init__,value_objects,exceptions,entities,hours,repository}.py` | CREATED |
| `app/application/timeclock/{__init__,use_cases}.py` | CREATED |
| `app/application/reporting/staff.py` | CREATED |
| `app/infrastructure/persistence/{shift_repo,staff_report_repo}.py` | CREATED |
| `app/presentation/api/v1/timeclock.py` | CREATED |
| `app/presentation/schemas/timeclock.py` | CREATED |
| `alembic/versions/0006_shifts.py` | CREATED |
| `tests/unit/test_timeclock.py` | CREATED (10) |
| `tests/integration/test_e2e_timeclock.py` | CREATED (7) |
| `tests/integration/test_e2e_staff_report.py` | CREATED (2) |

### Backend — editados
| File | Action |
|---|---|
| `app/infrastructure/persistence/models.py` | `ShiftORM` + `Tenant.standard_workday_minutes` |
| `app/infrastructure/persistence/mappers.py` | shift mappers + tenant field |
| `app/domain/tenant/entities.py` | `standard_workday_minutes` |
| `app/container.py` | wiring shift repo + use cases + staff read model |
| `app/presentation/errors.py` | mapeo excepciones de fichaje |
| `app/presentation/api/v1/reports.py` + `schemas/reports.py` | endpoint `/reports/staff` |
| `app/main.py` | router timeclock |
| `tests/integration/conftest.py` | `_TABLES` ← `shifts` |

### Frontend — nuevos
| File | Action |
|---|---|
| `api/{timeclock-api,types-timeclock}.ts` | CREATED |
| `hooks/use-timeclock.ts` | CREATED |
| `lib/timeclock.ts` | CREATED |
| `components/shell/clock-toggle.tsx` | CREATED (widget topbar) |
| `features/timeclock/staff-page.tsx` | CREATED (página Personal) |
| `api/timeclock-api.test.ts` + `lib/timeclock.test.ts` | CREATED (9) |

### Frontend — editados
| File | Action |
|---|---|
| `services/services-{context,provider}.tsx` + `test/test-utils.tsx` | registrar `timeClockApi` |
| `components/shell/app-shell.tsx` | `ClockToggle` en topbar |
| `components/shell/nav-config.ts` | nav "Personal" |
| `app/router.tsx` | ruta `/app/staff` (OWNER/MANAGER) |

## Deviations from Plan
- **T6 diferido a Fase 5.5.** El plan ya lo describe como incremental y aislado
  detrás del port `PresenceToken`; T1–T5 son una entrega coherente y shippable
  (fichaje propio + corrección + reporte). El toggle base (`source=SELF`) ya es
  el fallback honor-system que T6 complementa, así que nada queda a medias.
- **Endpoints `/clock-in` + `/clock-out` además del `/punch`.** El plan permitía
  "o /clock-in+/clock-out"; expuse ambos: el toggle `/punch` para el widget y los
  estrictos para poder rechazar doble-entrada / salida-sin-abrir con `code` estable
  (lo exige el criterio de aceptación).
- **Overtime agregado en Python** dentro del read model (reusa el `daily_overtime`
  puro del dominio) en lugar de SQL, para una sola fuente de verdad. Días
  bucketeados por fecha de `clock_in_at` (UTC) — suficiente para el reporte MVP.

## Issues Encountered
- Un `Edit` apuntó al archivo equivocado (import de `ShiftORM` va en `mappers.py`,
  no en `models.py`) — corregido en el acto.
- ruff reordenó imports en la migración `0006` (esperado, autofix).

## Next Steps (T6 — Fase 5.5, opcional)
- [ ] `PresenceToken` port + `HmacPresenceToken` (token rotativo por tiempo,
      single-use por (token,user), rate-limit) + tabla `used_presence_tokens` + Selector `presence_provider`.
- [ ] Credencial de dispositivo por local (provisión por OWNER; molde = conectar integración) + `GET /timeclock/presence/current`.
- [ ] `POST /timeclock/punch` acepta `{presented}` → `verify` → toggle `source=PRESENCE`.
- [ ] Pantalla display (QR + código rotando) + scanner/​input en la app.
- [ ] Code review (`/code-review`) + PR/merge a `main`.
