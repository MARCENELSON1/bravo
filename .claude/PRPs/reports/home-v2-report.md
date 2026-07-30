# Implementation Report: Home v2 — dashboard de 7 niveles

**Fecha:** 2026-07-30 · **Rama:** `feat/home-v2`

## Summary
El dashboard (Inicio) se rearmó a la jerarquía de 7 niveles del spec, **frontend-only, sin backend ni migraciones**. Reusa los hooks existentes + `GET /finance/movements` (de Finanzas v2) + el componente `RecentMovements`.

## Validación
| Check | Estado |
|---|---|
| Build (tsc+vite) | ✅ |
| Tests front | ✅ 125 passed (6 nuevos: dailyVerdict + tomorrowTask) |
| Lint | ✅ |
| Backend | N/A (sin cambios) |

## Lo entregado (7 niveles)
1. **Hero "Tu ganancia de hoy"** — `net` del día en grande (rojo si <0) + mensaje contextual (`dailyVerdict`: buen día / normal / para revisar, con % vs ayer de la serie diaria).
2. **3 números** — Facturaste / Gastaste / Margen, con explicación 1 línea ("de cada $100, $X son ganancia").
3. **Cobros por canal** (payment mix) — bruto, con nota de que no se descuenta comisión.
4. **Alerta del día** (máx 1) — top diagnostic alert/warn; oculta si no hay.
5. **Progreso del mes** — proyección de cierre + gráfico 7 días.
6. **Últimos 5 movimientos** — reusa `/finance/movements`.
7. **Tarea para mañana** — `tomorrowTask` (acción del diagnostic más severo) + botón "Entendido" (estado local).

Helpers puros nuevos: `daily-verdict.ts`, `tomorrow-task.ts` (unit-testeados).

## Desviaciones / diferidos (por falta de dato, no de alcance)
- **Cobros netos de comisión**: `payments` no guarda fee → se muestra bruto (con nota). Fase futura.
- **Barra hacia objetivo mensual**: no hay objetivo configurable → se mantiene solo la proyección.
- **Botón "Cargar efectivo" en el Home**: el arqueo vive en `/app/caja`; no se duplicó el flujo.
- **"Entendido" no persiste** en backend (estado local del día).
- **% vs ayer** usa facturación (serie diaria), no el neto de ayer (no hay neto por día).

## Next Steps
- [ ] Revisión visual en el navegador (claro/oscuro).
- [ ] Próxima pantalla por ROI: Productos v2 (grande) o Reportes/Fase 10.
