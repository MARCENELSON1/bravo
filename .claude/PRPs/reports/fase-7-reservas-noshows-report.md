# Implementation Report: Fase 7 — Reservas + No-shows (Reservation)

## Summary
Gestión de **reservas** con **agenda por día/turno/mesa** y un ciclo de vida tipo máquina de estados
(PENDING → CONFIRMED → SEATED → COMPLETED, o CANCELLED / NO_SHOW). Nuevo dominio `reservation`: entidad
`Reservation` (cliente + N personas + fecha/hora + turno ALMUERZO/CENA + mesa opcional) con transiciones validadas,
persistencia con RLS, API REST (front of house) y una página de agenda con acciones por estado. Genera la fuente de
dato para el futuro KPI de no-shows (Capa 2 / Fase 9). Prioridad PRD: *Could*.

## Assessment vs Reality

| Metric | Predicted (Plan) | Actual |
|---|---|---|
| Complexity | Baja-media (CRUD + máquina de estados, sin cross-aggregate) | Coincide — directo sobre moldes (Order/Inventory/Table) |
| Confidence | Alta en los 4 tramos | Confirmado; sin sorpresas |
| Files Changed | ~25 nuevos/editados | 31 archivos (1744+ líneas) |

## Tasks Completed

| # | Task | Status | Notes |
|---|---|---|---|
| T1 | Dominio reservation | ✅ Complete | Entity + transiciones + VOs + port; 12 tests |
| T2 | Persistencia + migración RLS | ✅ Complete | ORM + mapper + repo + migración 0009 (RLS) reversible |
| T3 | Use cases + API + RBAC | ✅ Complete | /reservations/* (FOH) + agenda con filtros; 8 e2e |
| T4 | Frontend | ✅ Complete | Página agenda + sheet + acciones; nav + ruta; 9 tests |

## Validation Results

| Level | Status | Notes |
|---|---|---|
| Static Analysis | ✅ Pass | ruff + mypy (205 archivos) limpios; tsc + eslint limpios |
| Unit Tests | ✅ Pass | 12 unit dominio (transiciones, party_size, reschedule) + 3 lib frontend |
| Build | ✅ Pass | `vite build` ok (warning de chunk preexistente) |
| Integration (e2e) | ✅ Pass | 8 e2e backend + 6 api frontend |
| Edge Cases | ✅ Pass | transición inválida (409), mesa inexistente (404), reschedule terminal, agenda por día/turno, RLS |
| Coverage | ✅ Pass | reservation dominio+aplicación 95% (≥80% requerido) |

## Files Changed (31)
**Backend nuevos:** `domain/reservation/{__init__,entities,value_objects,exceptions,repository}.py`,
`application/reservation/{__init__,use_cases}.py`, `infrastructure/persistence/reservation_repo.py`,
`presentation/api/v1/reservations.py`, `presentation/schemas/reservations.py`,
`alembic/versions/0009_reservations.py`, `tests/unit/test_reservation.py`,
`tests/integration/test_e2e_reservations.py`.
**Backend editados:** `models.py`, `mappers.py`, `container.py`, `main.py`, `presentation/errors.py`,
`tests/integration/conftest.py`.
**Frontend nuevos:** `api/{types-reservations,reservations-api,reservations-api.test}.ts`,
`hooks/use-reservations.ts`, `lib/{reservations,reservations.test}.ts`,
`features/reservations/reservations-page.tsx`.
**Frontend editados:** `services/services-{context,provider}.tsx`, `test/test-utils.tsx`,
`components/shell/nav-config.ts`, `app/router.tsx`.

## Deviations from Plan
- **Ninguna estructural.** Implementado como estaba planeado. Detalle menor: las transiciones del ciclo de vida
  comparten una base `_ReservationTransition` (load → `getattr(reservation, action)()` → save) para no repetir
  cinco use cases casi idénticos; cada transición pública sigue siendo su propia clase (DI por endpoint).
- `UpdateReservation` (reschedule) no edita `note` (la nota se setea al crear) — alineado con `Reservation.reschedule`.

## Issues Encountered
- **`list` como nombre de método** en el port: ya conocido de Fase 6; acá no hubo conflicto porque ningún método
  posterior a `list` referencia `list[...]` (add/save devuelven None).
- **Archivos editados por linters/checkout** entre tramos (container/models/main/mappers): se releyeron antes de
  cada Edit; sin pérdida.

## Tests Written

| Test File | Tests | Coverage |
|---|---|---|
| `tests/unit/test_reservation.py` | 12 | transiciones válidas/ilegales, party_size, reschedule |
| `tests/integration/test_e2e_reservations.py` | 8 | happy path, no-show, transición inválida 409, mesa 404, reschedule, agenda día/turno, RLS |
| `frontend/src/api/reservations-api.test.ts` | 6 | métodos del cliente (create/list/confirm/no-show/update) |
| `frontend/src/lib/reservations.test.ts` | 3 | labels, variantes de badge, toReservedAtIso |

## Next Steps
- [ ] Code review via `/code-review`
- [ ] Merge a `main` (rama `feat/fase-7-reservas-noshows`)
- [ ] Validación en vivo: cargar una agenda real y recorrer el ciclo (confirmar/sentar/no-show)
- [ ] Fase 8 (modelo canónico + read models) — puede consumir no-shows / agenda
