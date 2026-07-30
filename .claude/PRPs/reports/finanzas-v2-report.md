# Implementation Report: Finanzas v2 — layout diseñado

**Fecha:** 2026-07-30 · **Rama:** `feat/finanzas-v2`

## Summary
Se rearmó la Pantalla Finanzas al layout de los mockups sobre el motor existente (Tandas A–F). Backend nuevo chico y sin migraciones (todo sale de `payments`): egresos por categoría con comparativo + movimientos recientes. Frontend reorganizado en niveles con hero, áreas de salud, variación de gastos, donut y últimos movimientos.

## Validación
| Check | Estado |
|---|---|
| Backend `pytest` | ✅ 371 passed (3 e2e nuevos: breakdown agrupa por categoría, movimientos IN/OUT, RLS aislado) |
| Frontend build (tsc+vite) | ✅ |
| Frontend tests | ✅ 119 passed (2 clientes API nuevos) |
| Lint | ✅ |

## Lo entregado
- **Backend:** `ExpenseBreakdownReadModel` (egresos OUTFLOW+CONFIRMED por categoría, ventana actual vs previa, delta) + `RecentMovementsReadModel` (últimos cobros/egresos), use cases, schemas, `GET /finance/expenses/breakdown` y `GET /finance/movements`, wiring en container. Sin migraciones.
- **Frontend:** hero "Tu ganancia neta del período" (+comparativo +proyección); 4 áreas de salud con semáforo + acción (Tu dinero, Costo comida, Costo personal, Mermas); "Los 3 gastos que más cambiaron"; donut de distribución de gastos (SVG a mano, clickeable); últimos movimientos (solo Hoy/Semana); KPIs del rubro + diagnósticos + margen por producto (existentes) reordenados. Nuevos componentes: `expense-donut`, `expense-changes`, `recent-movements`.

## Desviaciones del plan (honestas)
- **Sparklines en KPIs: NO implementadas** en esta pasada (para acotar el alcance). Quedan pendientes.
- **6ª área "Mejores días": diferida** — necesita agregación de facturación por día de semana que no existe aún. Se entregaron 4 áreas de salud (las derivables de KPIs). "Proveedores" quedó cubierto por la card "3 gastos que más cambiaron" en vez de una 6ª tarjeta.
- **Donut clickeable:** resalta el segmento (atenúa los demás) pero **NO filtra toda la pantalla** por categoría todavía (es más complejo; diferido).
- **Consolidación:** hero y áreas se hicieron inline en `finance-page.tsx` en vez de componentes separados (menos archivos, mismo resultado).

## Issues resueltos durante la implementación
- `POST /expenses` requería `method` (PaymentMethod) — se agregó al helper de test.
- GroupingError de Postgres al agrupar por `coalesce(category, 'Otros')` — se agrupa por la columna cruda y el None→"Otros" se resuelve en Python.

## Pendientes para una próxima pasada
- Sparklines de 30 días en los KPIs money.
- Área "Mejores días" (requiere serie de facturación por día de semana).
- Filtrar la pantalla completa al clickear un segmento del donut.
- Revisión visual fina (donut/hero) en claro y oscuro — no verificable sin display en esta sesión.

## Next Steps
- [ ] Revisión visual en el navegador (claro/oscuro, anchos).
- [ ] Según el doc de cobertura, la próxima pantalla de mejor ROI es **Home v2**.
