# Plan: Productos v3 — Fase 6, "Hero verificable + gate de cobertura ≥70%" (T8)

## Summary
Feature **chica**, casi todo frontend sobre datos que **Fase 3 ya emite**. El hero de
Productos ("Tu carta") solo muestra **conclusiones de plata** ("…te dejaron $X", "los 3
que más plata te dejan", "Te dejan $X" por categoría) **si la cobertura del tenant es
≥70%**; por debajo, las reemplaza por **"te faltan N platos con costo confirmado"** + CTA
"Cargar compras" → `/app/stock`. Regla 6: umbral definido **una vez**. Sin migración, sin
DI, `costing.py` intacto → paridad por construcción.

**Alcance:** solo **T8 (hero + gate)**. El hermano **T6 (rotación por sobre-índice)** queda
fuera (otro plan). **NO depende de Fase 4** (per-categoría, no mergeada): el gate depende
de la COBERTURA (Fase 3, mergeada), no de la clasificación; el hero lee la salida de
`classifyMenu` sin importar su versión.

## Ya existe (reusar) vs gap
**Ya existe:** `GET /inventory/food-cost` emite `coverage_bps`/`confirmed_count`/`total_count`
(`food_cost_repo.py:268-278`); `FoodCostReportDTO` los tiene (`types-inventory.ts:129-135`);
el hero ya muestra "N de M confirmados" (`menu-engineering-view.tsx:76-82`);
`confirmedMargin()`/`topEarners()` ya excluyen estimados (`menu-engineering.ts:70-82`); la
constante **`COVERAGE_GATE_BPS = 7000`** existe (`value_objects.py:13`) y **nadie la consume**.

**Gap:** (1) nadie compara la cobertura contra el umbral; (2) el hero no gatea (top-earners y
"Te dejan $X" per-categoría se muestran siempre); (3) no hay empty-state de sub-cobertura + CTA.

## Decisiones
- **(a) Dónde:** el gate vive en el hero "Tu carta" de `menu-engineering-view.tsx` (no card
  nueva, no toca `products-page.tsx`). **El Home NO se gatea** — verificado: `DashboardSummaryDTO.net`
  es caja financiera (ventas−egresos), y `dailyVerdict` consume ese `net` + variación de
  facturación; **ninguno deriva del food cost** → no se infla con costos estimados. La única
  superficie inflable es menu engineering → hero de Productos.
- **(b) Umbral:** consumir `COVERAGE_GATE_BPS` en el read model y **surface `coverage_ok: bool`**
  en la respuesta (definido una vez en el dominio; el front lee un bool, nunca hardcodea 7000).
  ~5 líneas backend. (Alt. solo-frontend con 0.70 hardcodeado: descartada por drift/Regla 6.)
- **(c) UX bajo el gate:** reemplazar la conclusión de plata por "Todavía no podemos decirte
  cuánto te dejó tu carta — te faltan {total−confirmed} platos con costo confirmado (vas
  {confirmed} de {total})" + CTA `Link`→`/app/stock`. Ocultar top-earners + "Te dejan $X"
  per-categoría. Mantener conteos, categorías, listas y la tabla de detalle (que ya etiqueta/
  grisa por plato — Fase 3).

## Files to Change
**Backend (aditivo, sin migración, sin DI):**
- `app/application/inventory/food_cost.py` — `FoodCostReport` +`coverage_ok: bool = True`.
- `app/infrastructure/persistence/food_cost_repo.py` — importar `COVERAGE_GATE_BPS`; tras
  `report_coverage` (~:271) `coverage_ok = report_coverage >= COVERAGE_GATE_BPS`; pasarlo a `FoodCostReport`.
- `app/presentation/schemas/inventory.py` — `FoodCostResponse` +`coverage_ok: bool = True`.
- `app/presentation/api/v1/inventory.py` — mapear `coverage_ok=report.coverage_ok`.

**Frontend:**
- `src/api/types-inventory.ts` — `FoodCostReportDTO` +`coverage_ok: boolean`.
- **CREATE** `src/features/products/coverage-gate.ts` — helper puro
  `coverageGate(report?) → { open, missing, confirmed, total }` (`open = report?.coverage_ok ?? true`;
  `missing = total_count − confirmed_count`). Sin report → `{ open: true }` (paridad, no gatea).
- **CREATE** `src/features/products/coverage-gate.test.ts` — tests puros.
- `src/features/products/menu-engineering-view.tsx` — `const gate = coverageGate(foodCost.data)`;
  hero: si `gate.open` agregar la frase de plata (`confirmedMargin(products)`), si no el empty-state
  + CTA; envolver top-earners (`:119-136`) y "Te dejan $X" per-categoría (`:101-105`) en `gate.open`.

## Step-by-Step
1. Backend: `coverage_ok` (read model → DTO → schema default True → endpoint). *Gotcha:* `total_count==0`
   ya da `report_coverage=10000` → `coverage_ok=True` (sin platos no hay conclusión que gatear).
2. `FoodCostReportDTO.coverage_ok` (requerido; el backend siempre lo emite).
3. `coverage-gate.ts` + test (open true/false, `missing` exacto, sin data → open true).
4. Gate en `menu-engineering-view.tsx` (hero + top-earners + per-categoría). *Gotcha:* no romper
   la rama `products.length===0`; `gate.open` default true evita parpadeo mientras carga `useFoodCost`.
5. Validación.

## Testing
- **Frontend (núcleo):** `coverage-gate.test.ts` — `coverage_ok:true→open`, `false→!open` con `missing`
  correcto, sin report → open (paridad).
- **Backend (paridad + borde):** suite completa sin cambios de números (solo campo aditivo);
  integration read model: `>=7000→True`, `<7000→False`, exacto 7000→True, 0 platos→True.

## Validation
```bash
# Backend (sin migración)
/Users/marce/Library/Caches/pypoetry/virtualenvs/bravo-backend-xQklV81L-py3.12/bin/ruff check --fix app tests
/Users/marce/Library/Caches/pypoetry/virtualenvs/bravo-backend-xQklV81L-py3.12/bin/python -m pytest
# Frontend
cd /Users/marce/Desktop/BRAVO/frontend && npm run build && npm run lint && npm test
```

## Acceptance
- [ ] `GET /inventory/food-cost` emite `coverage_ok = report_coverage_bps >= COVERAGE_GATE_BPS`
  (consume la constante del dominio; sin migración, sin DI, sin cambio de matemática).
- [ ] Hero ≥70%: muestra conclusión de plata + top-earners + "Te dejan $X" per-categoría.
- [ ] Hero <70%: sin conclusión de plata; "te faltan N platos con costo confirmado (vas X de M)" +
  CTA "Cargar compras"→`/app/stock`; top-earners y per-categoría ocultos; conteos/tabla intactos.
- [ ] Home NO gateado (sin cambios en `dashboard-page.tsx`/`daily-verdict.ts`).
- [ ] Umbral una sola vez (dominio); front nunca hardcodea 70%. Paridad backend verde.

## Diferido
T6 rotación por sobre-índice; `gate_bps` en la API (solo si el copy muestra el objetivo);
denominador "todos los productos" (se mantiene el de food-cost = platos con receta); nudge de
cobertura en onboarding sin ventas.

## Rollback
Revertir código (cero migración). `coverage_ok` aditivo default True → si el front no lo lee,
comportamiento = hoy.

### Critical Files
- frontend/src/features/products/menu-engineering-view.tsx
- frontend/src/features/products/coverage-gate.ts (nuevo + .test.ts)
- backend/app/infrastructure/persistence/food_cost_repo.py
- backend/app/application/inventory/food_cost.py
