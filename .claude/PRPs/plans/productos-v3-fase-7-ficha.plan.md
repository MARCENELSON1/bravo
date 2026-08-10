# Plan: Productos v3 — Fase 7, "Ficha del producto" (detalle del plato)

## Summary

La Ficha es **casi enteramente una composición de frontend** sobre endpoints que **ya existen y ya están wired** (food cost, drill-down de ventas, histórico de precios, sugerencia de precio, receta con versión, histórico de costo de insumo). La Fase 2 (2A/2B/2C/2D) fue diseñada explícitamente para *dejar el dato disponible* y **diferir el display a esta fase** (`2d-versionado.plan.md`: *"El display del histórico … es Fase 7 (Ficha completa), no 2D"*).

El delta real es minúsculo y **sin migración**:
- **Backend: 0 migraciones, 0 tablas.** Todo lo que la Ficha consume ya está persistido (`sale_facts` congela `food_cost_amount`/`recipe_version`, `stock_movements` congela `unit_cost_amount` por compra, `product_price_changes` guarda el historial). La migración **0028 no se usa** en esta fase.
- **Un (1) gap de frontend-plumbing real**: el endpoint `GET /inventory/ingredients/{id}/cost-history` **existe en backend** (`inventory.py:232-254`) pero **no tiene cliente ni hook** en el frontend (`inventory-api.ts` no lo expone). Hay que agregar el método de cliente + hook + tipo DTO.
- **Un (1) campo de tipo desincronizado**: el backend ya devuelve `RecipeResponse.version` (`schemas/inventory.py`, `products.py:201`) pero `RecipeDTO` del frontend (`types-inventory.ts`) **no tiene** `version`. Agregar el campo.
- **Una (1) adición backend OPCIONAL y fina** (sin migración): exponer `recipe_version` por línea en `ProductDetail` para marcar "acá cambiaste la receta" en el gráfico de costo-en-el-tiempo. El dato ya está en `sale_facts.recipe_version` (2D); solo hay que surface-arlo en el read model + DTO + schema.

Todo lo demás (desglose de receta con costos, gráfico de costo del plato en el tiempo, alertas "el insumo X subió Y%", aviso "compras viejas >60d", panel de precios con aplicar) se **deriva en el cliente** de datos ya disponibles. **Cero cambios en `costing.py`, cero DI backend** (salvo que se haga el opcional, que tampoco toca DI).

> Honestidad de alcance (igual criterio que 2D): **no fabricar feature**. La Ficha v1 = un `Sheet`/drawer de composición + 2 piezas de plumbing frontend + 1 add backend opcional. El grueso es UI.

## What the PRD asks vs defers (quoted)

No hay un ticket "Ficha" suelto; es **Fase 7 (T7)**. Citas exactas del PRD (`productos-v3.prd.md`):

**Lo que pide:**
- Tabla de fases, fila 7 (línea 133): *"Ficha completa | Receta con desglose + histórico de costos versionado + historial de precios + alertas de ingrediente ("el bife subió 12%") + "costos viejos si no cargás compras hace 60d" (T7) | pending | - | 2, 3"*.
- Phase Details (líneas 170-173): *"**Goal**: La ficha del plato como herramienta de decisión. **Scope**: Desglose de receta + recetas anidadas (ya ✅) + rendimiento del mes (con cobertura) + histórico de costos desde snapshots versionados + historial de precios + alertas de ingrediente + aviso de costos viejos (compras >60d). **Success signal**: El dueño ve por qué cambió el costo de un plato y qué ingrediente lo movió."*
- MoSCoW (línea 79): *"Should | Ficha completa + alertas de ingrediente (T7) | "El bife subió 12%, perdés $4/plato" es muy vendible"*.

**Lo que difiere / condiciona:**
- **Depende de Fase 2 y Fase 3** (col. `Depends` = "2, 3"). **Fase 2 está mergeada; Fase 3 (estado estimado/confirmado + cobertura, T1.7) NO.** Por lo tanto el *"rendimiento del mes (con cobertura)"* y el gate de *cobertura ≥70%* que requieren `cost_confirmed` **se difieren** hasta que Fase 3 exista. La Ficha v1 muestra los números disponibles sin el semáforo estimado/confirmado. (Se documenta como dependencia, no se fabrica el estado.)
- **Snapshot item-level de receta** ("ver la receta como estaba en cada venta") ya fue **diferido en 2D**: para v1 la Ficha muestra la receta **actual** + el **número** de costo histórico congelado (`sale_facts`); no reconstruye la receta vieja. Se mantiene diferido salvo pedido explícito.
- **Costo de mano de obra / tiempo de preparación por plato** (PRD línea 26): *"se nombra en la ficha como pendiente, no se calcula"*. Se muestra como texto "pendiente", no se calcula.

## What already exists vs what's a real gap (endpoint-by-endpoint)

| Dato de la Ficha | Endpoint backend | Cliente/hook/tipo FE | Estado |
|---|---|---|---|
| Food cost bruto + "te deja" (margen neto) + food-cost % por plato | `GET /inventory/food-cost` | `foodCost()` / `useFoodCost()` / `FoodCostReportDTO` | **EXISTE E2E** |
| Drill-down de ventas del plato + agregados | `GET /finance/products/{id}?from&to` | `productDetail()` / `useProductDetail()` / `ProductDetailDTO` | **EXISTE E2E** |
| Perf del plato (unidades, sales, margen) | `GET /analytics/products` | `useProductPerformance()` | **EXISTE E2E** |
| Receta (items) **+ versión** | `GET /products/{id}/recipe` | `getRecipe()` / `useRecipe()` / `RecipeDTO` | **Endpoint OK; `RecipeDTO.version` FALTA (gap fino de tipo)** |
| Nombres/costos de insumos y preparaciones | `GET /inventory/ingredients`, `/inventory/preparations` | `useIngredients/usePreparations` | **EXISTE E2E** |
| Histórico de costo del insumo | `GET /inventory/ingredients/{id}/cost-history` (`inventory.py:232-254`) | **FALTA cliente+hook+DTO** | **GAP REAL (solo plumbing FE)** |
| Historial de precios del plato | `GET /products/{id}/price-history` | `priceHistory()` / `useProductPriceHistory()` | **EXISTE E2E** |
| Sugerencia de precio + aplicar | `GET /products/pricing`, `PUT /products/{id}/price` | `pricing()`/`updatePrice()` | **EXISTE E2E** |
| `recipe_version` **por línea** de venta | mismo `GET /finance/products/{id}` | `finance_repo.py` no lo emite; `ProductSaleLine` no lo tiene | **GAP OPCIONAL (add fino sin migración)** |

**Conclusión**: de ~8 fuentes, **6 existen E2E**, **1 es plumbing puro de frontend** (cost-history), **1 es un campo de tipo desincronizado** (`RecipeDTO.version`), y **1 es un add backend opcional sin migración** (`recipe_version` por línea). **No se necesita migración 0028. No se toca `costing.py`. No se toca el DI container.**

## Design decision (recommended + alternatives + deferred)

### ✅ Recomendado — Ficha como `Sheet` de composición + 2 piezas de plumbing FE + 1 add backend opcional

**Estructura UI**: un componente `ProductFicha` (drawer `Sheet`, mirror de `RecipeSheet` en `product-catalog.tsx:131-151`) abierto desde una acción "Ficha" en cada fila del catálogo. Carga on-demand (`enabled` por `open`, mirror de `finance-page.tsx:290`). Secciones (se pueden componer con `GlassCard`/`Separator` existentes, o `tabs` vía shadcn):

1. **Resumen**: precio, costo (bruto), "te deja" (margen neto), food-cost % — de `useFoodCost()` (fila del plato) + unidades del período de `useProductPerformance()`. Reusa la semántica del catálogo (`catalog-rows.ts:24-34`).
2. **Receta con desglose**: `useRecipe(id)` (items) + `useIngredients()`/`usePreparations()` para nombres y costo unitario por línea; recetas anidadas ya resueltas por el motor (solo display). Botón "Editar receta" reusa `RecipeEditor`.
3. **Costo en el tiempo**: se **deriva** de `useProductDetail(id, período)` — `food_cost_amount / quantity` por línea, agrupado por día → sparkline SVG inline (sin dependencia nueva). Es el costo congelado punto-en-el-tiempo (2D). *(Con el add opcional, se marcan los cambios de `recipe_version`.)*
4. **Insumos y alertas**: por cada insumo de la receta, `useIngredientCostHistory(ingredientId)` (nuevo hook) → derivar "subió Y%" (primer vs último punto) y "compras viejas" (último `occurred_at` > 60 días). Lógica **pura y testeable** en `product-ficha.ts` (mirror `menu-engineering.ts`/`catalog-rows.ts`).
5. **Precios**: `useProductPriceHistory(id)` + fila de `usePricingInsights()` (sugerido/rezagado) + `useUpdateProductPrice()` para aplicar — reusa lo que hace `pricing-inflation-card.tsx`.

**Plumbing backend/tipos (mínimo):**
- FE: `InventoryApi.ingredientCostHistory(id)` + `useIngredientCostHistory(id)` + `IngredientCostPointDTO`.
- FE: `RecipeDTO.version?: number`.
- **Opcional** BE: `ProductSaleLine.recipe_version` → `ProductSaleLineResponse` → `ProductSaleLineDTO` (surface del campo ya congelado; **sin migración**).

**Por qué esta**: (a) máximo reuso — 6 de 8 fuentes ya E2E; (b) cero migración, cero `costing.py`, cero DI; (c) la lógica de alertas/derivaciones es pura → testeable con `npm test` sin backend; (d) el drawer on-demand no agrega carga a la lista del catálogo.

### Alternativas
- **A — Endpoint agregador `GET /products/{id}/ficha`**. Contra: duplica lógica que ya vive en 4 read models probados; agrega superficie + DI + tests por latencia marginal (drawer on-demand). **Diferida**.
- **B — Chart con librería (recharts/visx)**. Contra: **no hay** lib de charts en `package.json`; agrega dependencia + peso al bundle. v1 usa **sparkline SVG inline**. **Diferida**.
- **C — Snapshot item-level de receta por venta**. Ya diferido en 2D; `sale_facts` ya congela el número. **Diferida**.

### Deferred (explícito)
- Estado **estimado/confirmado + cobertura** (gate ≥70%): **depende de Fase 3 (no mergeada)** → fuera de v1.
- **Costo de mano de obra / tiempo de prep**: texto placeholder "pendiente".
- Marcadores de `recipe_version` en el gráfico: **opcional** (add fino).
- Endpoint agregador (Alt. A) y lib de charts (Alt. B).

## Patterns to Mirror (file:line)

- **Drawer per-producto desde el catálogo** — `product-catalog.tsx:131-151` (`RecipeSheet`: `Sheet`+`SheetTrigger`+carga condicional `open ? … : null`).
- **Carga on-demand con `enabled`** — `finance-page.tsx:289-290` + `use-finance.ts:36-43`.
- **Merge/derivación pura y testeable** — `catalog-rows.ts:17-61` y `menu-engineering.ts:26-73`. El nuevo `product-ficha.ts` sigue este molde con su `.test.ts`.
- **Cliente API + hook nuevos** — `inventory-api.ts:65-67` (`foodCost`) como molde de `ingredientCostHistory`; `use-inventory.ts:24-27` (`useFoodCost`) como molde de `useIngredientCostHistory`.
- **Panel de precios con aplicar** — `pricing-inflation-card.tsx` (usa `usePricingInsights`/`useProductPriceHistory`/`useUpdateProductPrice`).
- **Money + %** — `product-catalog.tsx:246-295` (`formatMoney`, "te deja" + food-cost %, nota IVA).
- **Surface de campo congelado (opcional BE)** — `finance_repo.py:114-124` (`ProductSaleLine`) + `finance.py:100-110` (`_detail_response`).

## Files to Change (por capa)

### Backend — **ninguno obligatorio** (0 migraciones, 0 DI)
- *(OPCIONAL, sin migración)* `finance/dtos.py` — `ProductSaleLine.recipe_version: int | None = None`.
- *(OPCIONAL)* `finance_repo.py` — emitir `recipe_version=r.recipe_version` en `ProductSaleLine` (la columna ya se selecciona vía `select(SaleFactORM)`).
- *(OPCIONAL)* `schemas/finance.py` + `api/v1/finance.py` — `ProductSaleLineResponse.recipe_version: int | None` en `_detail_response`.
- **Migración 0028**: **NO se crea.**
- **DI (`container.py`)**: **sin cambios.**

### Frontend — el grueso
- **MODIFY** `frontend/src/api/types-inventory.ts` — `RecipeDTO.version?: number`; nuevo `IngredientCostPointDTO { occurred_at: string; unit_cost_amount: number; currency: string }`.
- *(opcional)* **MODIFY** `frontend/src/api/types-operations.ts` — `ProductSaleLineDTO.recipe_version?: number | null`.
- **MODIFY** `frontend/src/api/inventory-api.ts` — método `ingredientCostHistory(id): Promise<IngredientCostPointDTO[]>` → `GET /inventory/ingredients/${id}/cost-history`.
- **MODIFY** `frontend/src/hooks/use-inventory.ts` — `useIngredientCostHistory(ingredientId: string | null)` (queryKey `["ingredient-cost-history", id]`, `enabled: Boolean(id)`).
- **CREATE** `frontend/src/features/products/product-ficha.ts` — lógica pura: `costSeriesByDay(lines)`, `ingredientCostAlert(points)`, `recipeBreakdown(recipe, ingredients, preparations)`.
- **CREATE** `frontend/src/features/products/product-ficha.test.ts` — tests puros.
- **CREATE** `frontend/src/features/products/product-ficha.tsx` — `ProductFicha` (`Sheet` con 5 secciones). Reusa `RecipeEditor`, `formatMoney`, hooks existentes.
- **MODIFY** `frontend/src/features/products/product-catalog.tsx` — la acción de fila "Receta" pasa a "Ficha" que abre `ProductFicha` (con edición de receta adentro). Pasar `period`.
- **MODIFY** `frontend/src/api/inventory-api.test.ts` — cubrir `ingredientCostHistory`.
- **CREATE** `frontend/src/components/ui/sparkline.tsx` — SVG inline puro (sin dependencia; accesible light/dark).

## Step-by-Step Tasks (ordenadas)

1. **FE plumbing: cost-history** — `types-inventory.ts` add `IngredientCostPointDTO`; `inventory-api.ts` add `ingredientCostHistory(id)`; `use-inventory.ts` add `useIngredientCostHistory` (`enabled`). *Gotcha*: `enabled: Boolean(id)`; endpoint ya tenant-scoped (RLS).
2. **FE tipo: `RecipeDTO.version`** — add `version?: number`. Backend ya lo emite.
3. **Lógica pura `product-ficha.ts`** — `costSeriesByDay`, `ingredientCostAlert` (primer vs último → %; `occurred_at` → días; umbral 60d), `recipeBreakdown`. *Gotcha*: 0/1 puntos (sin alerta), división por cero, ISO → agrupar por `slice(0,10)`.
4. **Tests puros** — `product-ficha.test.ts`. `npm test`.
5. **Componente `ProductFicha.tsx`** — `Sheet` con 5 secciones; hooks existentes + `useIngredientCostHistory` por insumo. *Mirror*: `RecipeSheet` + `finance-page.tsx:289-324`. *Gotcha*: on-demand (`open ? … : null`); evitar N requests hasta abrir la sección de insumos; reusar `RecipeEditor`.
6. **Wire en el catálogo** — `product-catalog.tsx`: la acción de fila abre `ProductFicha`; pasar `period`. *Gotcha*: no romper filtro/tabla; la Ficha es un `Sheet`, no una ruta nueva.
7. **Sparkline** — `sparkline.tsx` SVG inline; accesible dark mode. Si se difiere, mini-tabla.
8. *(OPCIONAL) recipe_version por línea* — `dtos.py` + `finance_repo.py` + `schemas/finance.py` + `finance.py`; FE `ProductSaleLineDTO.recipe_version?`. *Gotcha*: **paridad** — nullable, no altera agregados.
9. **Validación** (abajo).

## Testing Strategy

**Frontend (gate principal):**
- **Unit puras** (`product-ficha.test.ts`): `costSeriesByDay`, `ingredientCostAlert` (%, stale >60d), bordes (0/1 punto, qty 0, receta vacía).
- **API client** (`inventory-api.test.ts`): `ingredientCostHistory` pega al endpoint con `auth: true`.
- **Gate**: `npm run build` + `npm run lint` + `npm test` verdes. `RecipeDTO.version?` opcional no rompe consumidores.

**Backend (solo si se hace el opcional recipe_version):**
- **Paridad**: suite completa verde sin cambios de números (metadata nullable).
- **Integration**: `GET /finance/products/{id}` devuelve `recipe_version` por línea; línea sin receta → `None`; tenant-scoped.

## Validation Commands
```bash
# Frontend (gate de la fase)
cd /Users/marce/Desktop/BRAVO/frontend && npm run build && npm run lint && npm test

# Backend — SOLO si se incluye el opcional (venv poetry)
/Users/marce/Library/Caches/pypoetry/virtualenvs/bravo-backend-xQklV81L-py3.12/bin/ruff check --fix app tests
/Users/marce/Library/Caches/pypoetry/virtualenvs/bravo-backend-xQklV81L-py3.12/bin/python -m pytest
# (NO se corre alembic: esta fase no agrega migración)
```
Cult UI/shadcn para componentes nuevos (Sheet ya presente; Tabs opcional). La Ficha no agrega queries backend nuevas (reusa read models tenant-scoped existentes).

## Acceptance Criteria
- [ ] Desde el catálogo, cada plato abre una **Ficha** (`Sheet`) con: resumen (precio/costo/te deja/food-cost %), desglose de receta con costo por línea (anidadas incluidas), costo del plato en el tiempo, historial de precios + sugerido + aplicar, y alertas de insumo.
- [ ] **Alerta "el insumo X subió Y%"** desde `GET /inventory/ingredients/{id}/cost-history` (nuevo cliente+hook FE); **aviso "compras viejas >60 días"** por insumo.
- [ ] `RecipeDTO.version` disponible en el frontend.
- [ ] **Sin migración, sin cambios en `costing.py`, sin cambios de DI.** Gate FE verde.
- [ ] Lógica de derivación (`product-ficha.ts`) cubierta por tests puros.
- [ ] *(si se incluye el opcional)* `GET /finance/products/{id}` emite `recipe_version` por línea; suite backend verde sin cambios de números.
- [ ] Los bits que dependen de Fase 3 (estado estimado/confirmado + cobertura) quedan **documentados como diferidos**, no fabricados.

## Risks & Rollback
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Fabricar scope (agregador, item-level, estado de Fase 3) | Media | Medio | Explícitamente diferido; v1 = composición FE + 2 plumbing + 1 opcional |
| Waterfall de requests al abrir (N insumos → N cost-history) | Media | Bajo | Carga on-demand; recetas con pocos insumos; React Query cachea por id |
| `RecipeDTO.version` opcional rompe consumidores | Baja | Bajo | Campo opcional; backend ya lo emitía; gate `npm run build` |
| Lib de charts infla el bundle | Baja | Bajo | v1 usa sparkline SVG inline |
| *(opcional)* `recipe_version` por línea altera Finanzas | Muy baja | Alto | Metadata nullable; no lo lee ningún agregado; test de paridad |

**Rollback**: revertir código frontend (cero migración → sin estado en riesgo). Si se hizo el opcional backend: revertir el campo `recipe_version` (aditivo/nullable, sin `downgrade`).

## Notes
- **Por qué la Ficha casi no toca backend**: 2D dejó `recipe_version` en `sale_facts` y el histórico en `stock_movements` **precisamente para que la Ficha lo consuma** ("2D deja la etiqueta; Fase 7 la usa"). La Ficha es el consumidor, no un productor.
- **El único endpoint "huérfano"** (`cost-history`, construido en 2D) ya está en backend completo — solo le falta el cliente+hook de frontend.
- **Dependencia honesta**: `Depends="2, 3"` implica que la Ficha *completa* (con cobertura estimado/confirmado) necesita Fase 3 (no mergeada). Esta v1 entrega lo que 1+2 habilitan y difiere el semáforo sin fabricarlo.

### Critical Files for Implementation
- frontend/src/features/products/product-catalog.tsx
- frontend/src/api/inventory-api.ts
- frontend/src/hooks/use-inventory.ts
- frontend/src/api/types-inventory.ts
- backend/app/infrastructure/persistence/finance_repo.py
