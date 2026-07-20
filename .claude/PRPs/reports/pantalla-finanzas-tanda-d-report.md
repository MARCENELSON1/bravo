# Reporte — Pantalla Finanzas Tanda D: Labor Cost desde horas reales

**Fecha:** 2026-07-04 · **Rama:** `feat/finanzas-tanda-d` → merge a `main`

## Qué se entregó
El KPI "Costo de personal" (y con él Prime Cost, Margen neto y Punto de equilibrio) pasa de un prorrateo del costo mensual configurado a **horas realmente fichadas × valor/hora de cada empleado**, sensible a horas extras y eficiencia de turnos.

- **`users.hourly_rate_amount`** (migración `0017_user_hourly_rate`, additiva y nullable; aplicada a dev, prod vía preDeploy) + entidad/mapper.
- **Port `LaborCostReadModel`** + `SqlAlchemyLaborCostReadModel`: Σ minutos de turnos CLOSED × rate/60, solo empleados con rate; tenant-scoped.
- **`GetAdvisorReport`**: labor real para el período actual Y el previo (comparativos consistentes); si nadie tiene rate o no hubo turnos → **fallback al mensual prorrateado** (comportamiento previo intacto). Como Finanzas compone al Asesor, ambos quedan consistentes.
- **`PUT /users/{id}/hourly-rate`** (OWNER/MANAGER) — use case `SetUserHourlyRate`; null borra el rate.
- **Staff report** expone `hourly_rate_amount` por fila; la página **Personal** suma la columna "Valor hora" editable (pesos → minor units, Enter/blur guarda, vacío borra).

## Validación
- Backend **358 passed** (5 nuevos): unit del override + fallback + sin read model; e2e con turno real insertado (labor = 4h × rate en `/advisor/report`, rate visible en `/reports/staff`, borrar rate vuelve al fallback) + aislamiento cross-tenant (404).
- Frontend **build + lint + 117 tests** (nuevo: cliente `setHourlyRate`).

## Notas
- Empleados sin rate no aportan al labor real cuando otros sí tienen (cargar todos los rates para un número completo) — documentado en el repo.
- El turno se atribuye al día en que empezó (mismo criterio que el staff report, UTC/MVP).

## Sigue
Tandas **E** (RevPASH + rotación de inventario, migr. `0018`) y **F** (snapshots, migr. `0019`).
