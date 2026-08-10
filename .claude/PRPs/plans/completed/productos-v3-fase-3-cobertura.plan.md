# Plan: Productos v3 — Fase 3, "Estado estimado/confirmado + cobertura de costos" (T1.7)

## Summary

Fase 3 es una tanda de **metadata + read model + display**, no de matemática de costo. El motor (`costing.py`) y el read model de food cost (`food_cost_repo.py`) ya calculan **dos** costos por plato con **dos mapas de costo** (bruto por merma, neto de IVA) — `food_cost_repo.py:97-119` y `:153-173`. Fase 3 agrega un **tercer mapa** ("costo confirmado", donde los insumos sin compra real contribuyen 0) y deriva la **cobertura** = `food_cost_confirmado / food_cost_total`. Es el patrón existente, extendido una vez más.

Hallazgos que fijan el alcance:

1. **Hoy NO existe estado estimado/confirmado.** `Ingredient` no tiene flag de confirmación (`entities.py:46-72`, `IngredientORM`).
2. **La confirmación es derivable exactamente de los datos que ya hay.** `CreateIngredient` deja un costo **estimado** (carga a mano). El primer `RegisterPurchase` aplica last-cost (`Ingredient.set_cost`) y **deja un `StockMovement` reason=PURCHASE con `unit_cost`**. Entonces: **insumo confirmado ⇔ tiene ≥1 movimiento PURCHASE**. El costo solo se mueve por compra → derivación exacta, sin drift.
3. **La cobertura se reusa del propio `food_cost`.** `coverage_bps = food_cost(items, confirmed_map) / food_cost(items, full_map)`, con `confirmed_map[id] = cost si tiene compra, si no Money(0)`. Preparaciones anidadas resueltas con `resolve_preparation_costs` sobre el mapa confirmado (componente sin confirmar aporta 0), igual que el mapa neto de IVA hoy. Cero matemática nueva salvo un ratio de 3 líneas gemelo de `food_cost_ratio_bps`.

**Recomendación honesta (mismo criterio que 2D/Fase 7): no fabricar feature ni migración.** Delta: (a) pure fn `coverage_bps` en `costing.py`; (b) `food_cost_repo.py` arma el mapa confirmado (una query PURCHASE tenant-scoped) y setea `cost_confirmed`/`coverage_bps` por fila + cobertura de tenant; (c) surface en DTO/schema/endpoint; (d) el frontend **etiqueta** (badge estimado/confirmado), **grisa** la plata de los platos estimados y los **excluye** de conclusiones de plata (hero, totales por categoría) — sin ocultarlos. `costing.py` matemático intacto, **sin migración 0028**, **sin cambio de DI**. Paridad por construcción para un tenant con todo confirmado.

> El "costo estimado por IA con desglose" (T1.7, prioridad **Could**, LLM Fase 9) y el **gate ≥70% del hero** (que el PRD asigna a **Fase 6**) **quedan fuera**. Fase 3 **produce** cobertura + estado por plato; Fase 6 lo consume en el hero.

## What the PRD asks vs defers (quoted)

Es la **Fase 3** de la tabla de fases. Citas de `productos-v3.prd.md`:

**Lo que pide:**
- Fila 3: *"Costo confirmado + IA | Estado estimado/confirmado + cobertura visible (Regla 6), costo estimado por IA con desglose (T1.7) | pending | with 4 | 2"*.
- MoSCoW: *"Must | Estado estimado/confirmado + cobertura visible (Regla 6, T1.7) | Nada de plata sobre costos inventados"*.
- Phase Details: *"**Goal**: Cero plata sobre costos inventados. **Scope**: Estado `cost_confirmed` (estimado/confirmado); los estimados no entran en conclusiones de plata y se muestran en gris; cobertura "N de M confirmados" visible; costo estimado por IA que devuelve desglose de ingredientes, reusando LLM de Fase 9. **Success signal**: Un plato con costo estimado no aparece en el hero ni suma a "te dejó $X"; la cobertura se muestra."*
- Success Metrics: *"Cobertura de costos confirmados | ≥70% de platos por tenant | `cost_confirmed=true / total productos`"*.
- User Flow: *"Hero … (solo si cobertura ≥70%; si no, "te faltan N platos con costo confirmado")"*.
- Technical Approach: *"Reglas de honestidad en un helper único (cobertura), no replicado por bloque."*

**Lo que difiere / condiciona:**
- **Costo estimado por IA con desglose** — prioridad **Could**; LLM Fase 9. **Diferido.**
- **Gate ≥70% del hero** — el PRD lo asigna a **Fase 6** (*"hero verificable + gate cobertura ≥70% (T8)"*). Fase 3 entrega la cobertura por tenant; el hero de Fase 6 la lee.
- **`cost_confirmed` "en producto"**: la fuente natural es por insumo (compra real); el plato hace roll-up (plato confirmado = todos sus componentes de costo confirmados).
- **Fase 7 lo esperaba**: `fase-7-ficha.plan.md` difirió *"Estado estimado/confirmado + cobertura (gate ≥70%): depende de Fase 3"*. Esta tanda desbloquea el badge de estado + cobertura en la Ficha.

## Design decision (recommended + alternatives + deferred)

### ✅ Recomendado — confirmación DERIVADA de compras, cobertura reusando `food_cost`, display honesto (etiquetar + grisar + excluir, nunca ocultar)

**(a) Confirmación derivada de la existencia de un movimiento PURCHASE — sin migración, sin flag.**
- Insumo **confirmado ⇔ tiene ≥1 `StockMovement` reason=PURCHASE**. Se agrega **una** query tenant-scoped en `food_cost_repo.py`: `select(distinct(StockMovementORM.ingredient_id)).where(tenant_id==, reason==PURCHASE.value)` → `confirmed_ids: set[str]`.
- **Por qué derivar y no un flag `cost_confirmed` (+migración):** fuente única sin drift (la compra existe o no); el backfill de un flag **sería esta misma query**; el roll-up a plato hay que computarlo igual; consistente con 2D/Fase 7 (derivar de `stock_movements` sin tabla). Una query agrupada barata por reporte.

**(b) Cobertura reusando el motor puro (dominio) + agregación en el read model.**
- **Dominio**: `coverage_bps(confirmed: Money, total: Money) -> int`, gemelo de `food_cost_ratio_bps` (`costing.py:150-160`): `10000 si total==0`, si no `round(confirmed.amount * 10000 / total.amount)`. **No** se toca `food_cost`, `resolve_preparation_costs`, `effective/net_effective_unit_cost`, `margin`.
- **Read model**: tercer mapa `confirmed_cost_by_ingredient = {id: cost si id in confirmed_ids else Money(0)}` (paralelo a `net_cost_by_ingredient`); `confirmed_cost_by_preparation = resolve_preparation_costs(...)`; por plato `confirmed_fc = compute_food_cost(...)` (paralelo a `gross_fc`/`net_fc`); `coverage_bps = coverage_bps(confirmed_fc, gross_fc)`, `cost_confirmed = coverage_bps >= CONFIRMED_PLATE_BPS`.

**(c) Umbral + comportamiento: ETIQUETAR + GRISAR + EXCLUIR, nunca OCULTAR.**
- **Per-plato (estricto)**: `cost_confirmed = coverage_bps == 10000`. Constante `CONFIRMED_PLATE_BPS = 10000`. Se muestra siempre `coverage_bps` para parciales.
- **Per-tenant (gate del hero, Fase 6)**: `report.coverage_bps = round(confirmed_plates * 10000 / total_plates)` + `confirmed_count`/`total_count`. El **70%** (`COVERAGE_GATE_BPS = 7000`) es solo el umbral de tenant del hero de Fase 6.
- **Display**: badge estado (Confirmado/Estimado) + `coverage_bps`; los estimados muestran su plata **en gris** (visible) y **no suman** a conclusiones de plata. **Nunca se ocultan** — el dueño debe ver el plato que le falta confirmar; el CTA es "cargá una compra".

**Por qué esta combinación**: sin migración, sin DI, `costing.py` matemático intacto → paridad por construcción; reusa el patrón de doble-mapa (tercera repetición, no arquitectura nueva); display puro y testeable en frontend; fuente única sin drift (Regla 6).

### Alternativas
- **A — Flag almacenado `cost_confirmed` en `Ingredient` + migración 0028** (true en el 1er `RegisterPurchase`, backfill). Pro: O(1), matchea el nombre del PRD, futuro para confirmar-a-mano/IA. Contra: drift, escritura extra, el backfill ES la derivación, roll-up igual. **Diferida** hasta que exista confirmar-a-mano o IA (ahí un enum `ESTIMATED/CONFIRMED/AI_ESTIMATED` en 0028+).
- **B — Cobertura por conteo de ingredientes** (nº confirmados/total). Contra: engaña (un insumo caro pesa igual que la sal). Ponderar por food cost es lo honesto y sale gratis del motor. **Descartada.**
- **C — Umbral per-plato al 70%** (`>= 7000`). Pro: menos fricción, un solo "70%". Contra: llamar "confirmado" a un plato con 30% adivinado roza la deshonestidad. **Documentada** (cambiar una constante); la cobertura% se muestra igual.
- **D — Surface de `cost_confirmed` también en `analytics_repo`** para el hero. Contra: duplica la determinación. El frontend ya cruza food-cost ↔ performance por `product_id`. **Diferida.**

### Deferred (explícito)
- Costo estimado por IA con desglose (T1.7 Could, LLM Fase 9).
- Gate ≥70% del hero → **Fase 6** (esta tanda deja `report.coverage_bps`/`confirmed_count`).
- Flag/estado almacenado (Alt. A) → cuando exista confirmar-a-mano/IA.
- Cobertura sobre productos sin receta: `total_count` = platos con receta; el denominador exacto de tenant es decisión del hero de Fase 6.

## Patterns to Mirror (file:line)
- **Doble mapa de costo (bruto vs neto) + doble `food_cost` por plato** — `food_cost_repo.py:97-119`, `:153-173`, `:182-195`. El mapa confirmado es el tercero, calcado.
- **Filtro por `reason`** — `stock_movement_repo.py:26-39` como molde de `distinct(ingredient_id) where reason=PURCHASE`.
- **Pure fn de ratio en bps** — `costing.py:150-160` (`food_cost_ratio_bps`) gemelo de `coverage_bps`.
- **Campo aditivo en DTO frozen** — `food_cost.py:13-27` (`FoodCostRow`/`FoodCostReport`).
- **Surface en schema+endpoint** — `schemas/inventory.py` (`FoodCostRowResponse`/`FoodCostResponse`) + `api/v1/inventory.py:208-229`.
- **Merge food-cost ↔ performance por product_id** — `catalog-rows.ts:22-34`.
- **Clasificación pura + test** — `menu-engineering.ts` + `.test.ts`; `catalog-rows.ts` + `.test.ts`; `ficha-logic.ts` + `.test.ts` (param opcional aditivo con paridad).
- **Badge de estado (frontend)** — `product-ficha.tsx` (Badge condicional) y `menu-engineering-view.tsx` (MenuRow).
- **Read model sin cambio de DI** — `container.py` (`food_cost_read_model`) — la query va dentro del read model.

## Files to Change (por capa)

### Domain
- **MODIFY** `costing.py` — pure fn `coverage_bps`. No se toca nada más.
- **MODIFY** `value_objects.py` — `CONFIRMED_PLATE_BPS = 10000`, `COVERAGE_GATE_BPS = 7000` (constantes).

### Application
- **MODIFY** `application/inventory/food_cost.py` — `FoodCostRow` (+`cost_confirmed: bool`, `coverage_bps: int`); `FoodCostReport` (+`coverage_bps`, `confirmed_count`, `total_count`).

### Persistence
- **MODIFY** `food_cost_repo.py` — query PURCHASE→`confirmed_ids`; mapa confirmado + resolución de preparaciones; `confirmed_fc`/`coverage_bps`/`cost_confirmed` por fila; agregación de reporte. **`compute_food_cost`/`resolve_preparation_costs` se llaman igual.**
- **NO migración 0028.** **DI sin cambios.**

### Presentation
- **MODIFY** `schemas/inventory.py` — `FoodCostRowResponse` + `cost_confirmed`/`coverage_bps`; `FoodCostResponse` + `coverage_bps`/`confirmed_count`/`total_count`.
- **MODIFY** `api/v1/inventory.py` — `get_food_cost` mapea los campos nuevos.

### Frontend
- **MODIFY** `types-inventory.ts` — `FoodCostRowDTO` + `cost_confirmed`/`coverage_bps`; `FoodCostReportDTO` + `coverage_bps`/`confirmed_count`/`total_count`.
- **MODIFY** `catalog-rows.ts` (+`costConfirmed`/`coverageBps`; merge aditivo) + `catalog-rows.test.ts`.
- **MODIFY** `product-catalog.tsx` — badge Estimado/Confirmado + grisado de Costo/Te deja cuando `!costConfirmed`.
- **MODIFY** `menu-engineering.ts` — `classifyMenu(rows, confirmedIds?)` (param opcional → paridad); `topEarners`/totales excluyen estimados + `.test.ts`.
- **MODIFY** `menu-engineering-view.tsx` — cruza `useFoodCost()` por `product_id`; "N de M confirmados"; hero/top excluyen estimados; badge + grisado.
- **MODIFY** `product-ficha.tsx` — Resumen: badge Estado + "Cobertura N%" (el bit que Fase 7 difirió).
- *(opcional)* **CREATE** `coverage.ts` + `coverage.test.ts` — helper puro `isConfirmed`/`coverageLabel` (Regla 6).

## Step-by-Step Tasks (ordenadas)
1. **Dominio `coverage_bps`** — gemelo de `food_cost_ratio_bps`; `total==0 → 10000`.
2. **Constantes** — `CONFIRMED_PLATE_BPS`/`COVERAGE_GATE_BPS` (comentar que 7000 lo usa Fase 6).
3. **DTOs** — `FoodCostRow`/`FoodCostReport` con los campos nuevos.
4. **Read model** — query PURCHASE→`confirmed_ids`; mapa confirmado + resolución; por fila `confirmed_fc`/`coverage_bps`/`cost_confirmed`; agregación de reporte. *Gotchas*: tenant-scoped + RLS; preparación confirmada = componentes confirmados (mask antes de `resolve`); `gross_fc==0` → coverage 10000; reporte 0 filas sin dividir por cero.
5. **Schema + endpoint** — response 1:1 con el DTO.
6. **Tipos frontend** — campos requeridos (el backend siempre los emite).
7. **Catálogo** — badge + grisado; no romper `filterCatalog`/`mergeCatalogRows`.
8. **Menu engineering** — `classifyMenu(rows, confirmedIds?)` aditivo; view cruza `useFoodCost`, muestra cobertura, excluye estimados. Paridad sin `confirmedIds`.
9. **Ficha** — badge estado + cobertura en Resumen.
10. **Tests + validación**.

## Testing Strategy (incl. paridad)
**Paridad (default / todo-confirmado == hoy):** suite backend completa verde **sin cambios de números** (`food_cost_amount`/`margin_amount`/`food_cost_ratio_bps` idénticos; solo campos nuevos). Tenant con todos los insumos con compra → `coverage_bps==10000`/`cost_confirmed==True` en cada fila. Frontend: `classifyMenu` sin/con `confirmedIds`-completo → mismos totales.

**Backend nuevos:** unit `coverage_bps` (0→10000, mitad→5000, CurrencyMismatch); integration read model (compra→confirmado; creación→estimado→aporta 0; plato 1 de 2 sin compra → parcial; preparación con componente sin compra → propaga); cross-tenant (compra de otro tenant no confirma); reporte (`confirmed_count`/`total_count` + vacío sin div0).

**Frontend:** `menu-engineering.test.ts` (paridad sin `confirmedIds`; parcial excluye estimados); `catalog-rows.test.ts`; `coverage.test.ts` si se extrae.

## Validation Commands (venv poetry)
```bash
# Backend (sin migración: 0028 NO se crea)
/Users/marce/Library/Caches/pypoetry/virtualenvs/bravo-backend-xQklV81L-py3.12/bin/ruff check --fix app tests
/Users/marce/Library/Caches/pypoetry/virtualenvs/bravo-backend-xQklV81L-py3.12/bin/python -m pytest

# Frontend
cd /Users/marce/Desktop/BRAVO/frontend && npm run build && npm run lint && npm test
```

## Acceptance Criteria
- [ ] `coverage_bps` (dominio puro) + `CONFIRMED_PLATE_BPS`/`COVERAGE_GATE_BPS`; `costing.py` matemático sin cambios.
- [ ] `GET /inventory/food-cost` emite por fila `cost_confirmed`+`coverage_bps` y por reporte `coverage_bps`/`confirmed_count`/`total_count`.
- [ ] Insumo con compra → confirmado; sin compra → estimado. Plato con ≥1 componente estimado → `cost_confirmed=false`, `coverage_bps<10000`.
- [ ] Catálogo, menu engineering y Ficha **etiquetan** estado, **muestran cobertura**, **grisan** la plata de estimados y los **excluyen** de conclusiones de plata — **sin ocultarlos**.
- [ ] **Sin migración, sin cambios en la matemática de `costing.py`, sin DI.** Paridad: tenant todo-confirmado idéntico a hoy.
- [ ] Cobertura/clasificación cubiertas por tests (front puros + read model back). Suite verde.
- [ ] Diferidos documentados: costo por IA (Could) + gate ≥70% del hero (Fase 6).

## Risks & Rollback
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| El mapa confirmado altera `food_cost`/`margin` | Muy baja | Alto | Tercer cómputo aislado; `gross_fc`/`net_fc` intactos; test de paridad |
| Confirmación derivada mal | Media | Medio | Test compra→confirmado, creación→estimado, roll-up de preparación |
| Query PURCHASE sin `tenant_id` | Baja | Alto | Filtro explícito + RLS; test cross-tenant |
| Fabricar scope (IA, gate del hero, flag) | Media | Medio | Diferido explícito |
| Hero excluye mal (paridad front) | Media | Bajo | `confirmedIds` opcional → sin él, hoy; tests de `classifyMenu` |

**Rollback**: revertir código (cero migración). Todo aditivo/identidad; sin `confirmedIds` el frontend vuelve a hoy.

## Notes
- **Por qué Fase 3 casi no toca el motor**: reusa `food_cost`/`resolve_preparation_costs` con un tercer mapa (confirmado) — el mismo doble-cómputo bruto/neto ya existente. Paridad por construcción.
- **Regla 6**: confirmado vive **una vez** en el read model; display **una vez** en un helper puro frontend.
- **Handoff a Fase 6**: `report.coverage_bps`/`confirmed_count`/`total_count` listos para el gate ≥70% del hero. Fase 3 produce; Fase 6 consume.

### Critical Files for Implementation
- backend/app/infrastructure/persistence/food_cost_repo.py
- backend/app/application/inventory/food_cost.py
- backend/app/domain/inventory/costing.py
- frontend/src/features/products/menu-engineering-view.tsx
- frontend/src/features/products/catalog-rows.ts
