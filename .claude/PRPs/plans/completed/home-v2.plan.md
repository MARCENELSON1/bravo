# Plan: Home v2 — dashboard al layout de 7 niveles

## Summary
Rearmar la Pantalla Inicio (dashboard) a la jerarquía de 7 niveles del spec, **sin backend nuevo**: reusa los hooks existentes + el `GET /finance/movements` ya creado. Dos sub-features del spec (cobros netos de comisión, barra hacia objetivo mensual) se **difieren** porque no hay dato: `payments` no guarda comisión y no existe un objetivo mensual configurable.

## User Story
Como dueño, quiero abrir la app después de un día largo y saber en 3 segundos si me fue bien (un número grande), de dónde viene, y qué hacer mañana — sin un dashboard lleno de gráficos.

## Problem → Solution
Hoy el dashboard muestra saludo + 5 KPIs + gráfico 7 días + recomendaciones IA + medios de pago + proyección, todo al mismo nivel. → Reencuadrar en la jerarquía: ganancia del día (hero) → 3 números que la explican → cobros del día → alerta → progreso del mes → últimos movimientos → tarea de mañana.

## Metadata
- **Complexity**: Medium (frontend-only, ~4-6 archivos)
- **Source**: research `wellnod-6-pantallas-cobertura.md` §HOME + `proyecto Well Nod 2026/Pantalla HOME` (7 niveles, doc solo texto)
- **Estimated Files**: ~5 frontend, 0 backend

## Contexto verificado
| Hecho | Detalle |
|---|---|
| Dashboard actual | `frontend/src/features/dashboard/dashboard-page.tsx` (solo OWNER/MANAGER via `RoleLanding`). Usa `useDashboard`, `useRevenueDaily`, `usePaymentMix`, `useFinanceOverview`. Ya tiene: saludo, 5 KPIs, gráfico 7d, Recomendaciones IA (diagnostics), medios de pago, proyección. |
| `DashboardSummary` DTO | `currency, sales (INFLOW confirmado), expenses (OUTFLOW confirmado), net (sales−expenses), active_orders, paid_orders, avg_ticket, payment_count`. → **hero = net; 3 números = sales/expenses/net**. |
| **Comisiones: NO existen** | `PaymentORM` no tiene fee/comisión por pago. → Nivel 3 "cobros netos de comisión": **diferir el neteo**, mostrar el bruto por canal (payment mix ya lo da). |
| **Objetivo mensual: NO existe** | No hay goal/target de facturación configurable. → Nivel 5 "barra hacia objetivo": **diferir la barra de objetivo**, mantener la proyección de cierre (`data.projection`). |
| Últimos movimientos | `GET /finance/movements` (`useRecentMovements`) YA existe + componente `RecentMovements` en `features/finance/recent-movements.tsx`. Reusar con `limit`≈5, ventana del día. |
| Estilo | `GlassCard`, tokens Wellnod, container `mx-auto max-w-7xl px-6 py-8`, patrón de sub-componentes hand-rolled (RevenueChart) ya en dashboard-page. |

## Patterns to Mirror
- **HOOKS + GlassCard**: dashboard-page.tsx actual (useDashboard/usePaymentMix/useFinanceOverview + tarjetas GlassCard).
- **Movimientos**: `features/finance/recent-movements.tsx` (ya hecho) + `useRecentMovements(window, enabled)`.
- **Diagnostics → alerta**: `topDiagnostics()` ya existe en dashboard-page (ordena alert→warn→healthy); Nivel 4 usa el primero.
- **Money**: `formatMoney` (@/lib/money).

---

## UX Design
### After (jerarquía)
```
Buen día, {nombre}                              {fecha}
┌──────────────────────────────────────────────┐
│ NIVEL 1 · Tu ganancia de hoy                  │
│   $ 128.400   🟢 Buen día — +12% vs ayer      │  ← hero, número grande + mensaje
├──────────────────────────────────────────────┤
│ NIVEL 2 · Facturaste $X · Gastaste $Y · Margen│  ← 3 números con explicación 1 línea
├──────────────────────────────────────────────┤
│ NIVEL 3 · Cobros de hoy por canal (bruto)     │  ← payment mix (neteo diferido)
│ NIVEL 4 · ⚠️ 1 alerta (si hay)                 │  ← top diagnostic
│ NIVEL 5 · Progreso del mes + proyección       │  ← proyección (barra-objetivo diferida)
│ NIVEL 6 · Últimos movimientos (5)             │  ← /finance/movements
│ NIVEL 7 · Tu tarea para mañana [Entendido]    │  ← 1 acción derivada del diagnostic
└──────────────────────────────────────────────┘
```

---

## Files to Change
| File | Action | Qué |
|---|---|---|
| `frontend/src/features/dashboard/dashboard-page.tsx` | UPDATE (rework) | Reordenar en los 7 niveles; hero de ganancia + mensaje contextual; 3 números con explicación; alerta única; tarea de mañana |
| `frontend/src/features/dashboard/daily-verdict.ts` | CREATE | Helper puro: dado net del día (y ayer si se puede), devuelve mensaje contextual ("mejor día / normal / para preocuparse") + tono. Unit-testeable |
| `frontend/src/features/dashboard/tomorrow-task.ts` | CREATE | Helper puro: deriva 1 acción concreta del top diagnostic / KPIs (determinista) |
| `frontend/src/features/dashboard/daily-verdict.test.ts` | CREATE | Tests del veredicto y de la tarea |
| (reusar) `recent-movements.tsx`, `useRecentMovements`, `topDiagnostics` | — | Sin cambios |

## NOT Building
- ❌ **Cobros netos de comisión** (Nivel 3): `payments` no guarda fee. Se muestra el bruto por canal; el neteo real necesita capturar la comisión por pago (fase futura, atada a integraciones de pago).
- ❌ **Botón "Cargar efectivo" en el Home** (Nivel 3): el arqueo/caja ya existe en `/app/caja`; por ahora, link a caja en vez de un flujo nuevo en el Home.
- ❌ **Barra hacia objetivo mensual** (Nivel 5): no hay objetivo configurable. Se mantiene la proyección de cierre; el objetivo es una fase futura (settings nuevo).
- ❌ Backend nuevo / migraciones — todo con datos existentes.
- ❌ Persistir el "Entendido" del Nivel 7 en el backend (estado local del día; persistencia server es opcional futura).
- ❌ Comparativo "vs ayer" exacto si no hay serie de ayer accesible barata — usar la serie diaria (`useRevenueDaily`) para derivar ayer si alcanza; si no, mostrar el veredicto sin el "%vs ayer".

---

## Step-by-Step Tasks

### Task 1 — Helper de veredicto diario (puro + test)
- **ACTION**: `daily-verdict.ts`: `dailyVerdict(netToday: number, netYesterday: number | null) -> { tone: "good"|"ok"|"bad"; message: string }`. Reglas: net<0 → bad ("día para revisar"); net>0 y (yesterday null o net≥yesterday) → good; si bajó vs ayer → ok. Mensaje en lenguaje del dueño, con %vs ayer si hay yesterday.
- **VALIDATE**: unit tests (net negativo, sin ayer, mejor que ayer, peor que ayer).

### Task 2 — Helper de tarea de mañana (puro + test)
- **ACTION**: `tomorrow-task.ts`: `tomorrowTask(diagnostics, kpis) -> string | null`. Toma el diagnostic de mayor severidad y devuelve su `action` (o una acción derivada del peor KPI). null si todo sano.
- **VALIDATE**: unit test (con alerta → acción; sin nada → null).

### Task 3 — Rework de dashboard-page en 7 niveles
- **ACTION**: Reordenar el JSX: (Header saludo+fecha) → (Hero ganancia del día `net` con `dailyVerdict`) → (3 tarjetas: Facturaste `sales` / Gastaste `expenses` / Margen `net` con explicación 1 línea) → (Medios de pago hoy — ya existe, aclarar "bruto") → (Alerta única: `topDiagnostics()[0]` si severidad alert/warn) → (Progreso del mes: proyección existente) → (`RecentMovements` con `useRecentMovements({from: inicio del día}, true)` limit 5) → (Nivel 7: tarea de mañana + botón "Entendido" con estado local `useState`).
- **MIRROR**: GlassCard + hooks existentes; `RecentMovements` reusado; `topDiagnostics` reusado.
- **GOTCHA**: para "vs ayer", derivar el net de ayer desde `useRevenueDaily` (facturación) — pero ayer necesita también egresos de ayer, que no vienen por día; **simplificar**: el hero compara facturación de hoy vs ayer (de la serie diaria) para el "%", y el mensaje de ganancia usa el `net` del día. Documentar la aproximación.
- **VALIDATE**: `npm run build` + revisión visual claro/oscuro.

### Task 4 — Validación integral
- **ACTION**: `cd frontend && npm run lint && npm run test && npm run build`. Manual: dashboard con datos reales; con día en pérdida (net<0) el hero se pone en rojo; sin diagnósticos, se ocultan alerta y tarea.
- Merge `--no-ff` a `main` + push.

---

## Testing Strategy
| Test | Input | Expected |
|---|---|---|
| dailyVerdict net<0 | net=-5000 | tone "bad" |
| dailyVerdict sin ayer | net=1000, null | tone "good", sin %|
| dailyVerdict mejor que ayer | net=2000, 1000 | tone "good", "+100%" |
| dailyVerdict peor que ayer | net=800, 1000 | tone "ok" |
| tomorrowTask con alerta | diagnostics=[alert] | devuelve su action |
| tomorrowTask todo sano | [] | null |
- Edge: sin ventas (net=0, todo "—"); rol no-OWNER no llega al dashboard (RoleLanding); "Entendido" oculta el bloque en la sesión.

## Validation Commands
```bash
cd frontend && npm run lint && npm run test && npm run build
```
EXPECT: verde. (Sin backend → no hace falta pytest, salvo regresión.)

## Acceptance Criteria
- [ ] Hero de ganancia del día + mensaje contextual (rojo si net<0).
- [ ] 3 números (facturó/gastó/margen) con explicación en 1 línea.
- [ ] Cobros por canal (bruto, con nota).
- [ ] Alerta única (top diagnostic) o ausente.
- [ ] Progreso del mes con proyección.
- [ ] Últimos 5 movimientos (reusa /finance/movements).
- [ ] Tarea de mañana + "Entendido".
- [ ] Helpers con tests; build + lint + tests verdes.

## Risks
| Risk | Prob | Impacto | Mitigación |
|---|---|---|---|
| "vs ayer" impreciso (no hay net diario) | Media | Bajo | Comparar facturación hoy/ayer de la serie diaria; el veredicto usa net del día; documentar |
| Diferir comisiones decepciona | Media | Medio | Es honesto (no hay dato); dejar claro "bruto" y anotar como fase futura |
| Rework rompe el dashboard actual | Baja | Medio | `npm run build` + tests + revisión visual; el dashboard ya tiene 117+ tests de front que deben seguir verdes |

## Notes
- **Frontend-only**: cero backend, cero migraciones. El único dato nuevo (movimientos) ya está.
- Deferrals (comisiones, objetivo mensual, botón cargar efectivo en Home, persistir "Entendido") son por falta de dato/estructura, no por alcance — anotados para fases futuras.
- Próxima pantalla por ROI tras Home v2: Productos v2 (grande) o Reportes/Fase 10.
