# Plan: Productos v3 — Fase 1 (Bugs P0)

## Summary
Arreglar los bugs visibles hoy en `/app/products`: un **selector de período único** que gobierna los bloques temporales (B1) — que además destapa/arregla el 422 enmascarado de menu engineering (`limit=500` > cap 100) causa raíz de la contradicción B1/B2 —, **columnas Costo/Te deja/Vendidos + buscador/filtros** en el catálogo (B6/B7), **validación de nombre** (B5) y **forzar la estación** en el alta (B4). Todo frontend salvo un ajuste chico de schema/validación en backend. Sin migraciones.

## User Story
Como **dueño (OWNER/MANAGER)**, quiero que **la pantalla Productos no se contradiga y que el catálogo me muestre costo, margen y vendidos filtrables**, para **poder decidir precios y qué platos empujar sin que los números me hagan desconfiar**.

## Problem → Solution
Bloques con ventanas distintas que se contradicen + catálogo que solo muestra precio + validaciones inexistentes → **una ventana global compartida**, catálogo con las columnas que importan y buscador, y validaciones mínimas en el alta.

## Metadata
- **Complexity**: Small–Medium (~10 archivos, casi todo frontend)
- **Source PRD**: `.claude/PRPs/prds/productos-v3.prd.md` — Fase 1
- **PRD Phase**: 1 (Bugs P0)
- **Estimated Files**: ~10
- **Sin migraciones.**

---

## UX Design

### Before
```
Productos
  [Catálogo alta form...]
  Menu engineering  → empty "no hay ventas en 30 días"  (¡en realidad 422 por limit=500!)
  Precios vs inflación | Rotación por día → "$15.894.600 sábado" (suma TODO el historial)
  Catálogo:  Nombre · Categoría · Estación · Precio · Estado · Receta
```

### After
```
Productos                                  [Hoy][Semana][Mes*][Trimestre]  ← período único
  [Catálogo alta form...]  (estación sin preselección; nombre validado)
  Menu engineering  → usa el período; limit=100 (sin 422)
  Precios vs inflación | Rotación por día  → Rotación usa el mismo período
  Catálogo:  [buscar…] [categoría ▾] [estado ▾]
    Nombre · Categoría · Estación · Precio · Costo · Te deja ($ y %) · Vendidos · Estado · Receta
```

### Interaction Changes
| Touchpoint | Before | After | Notes |
|---|---|---|---|
| Período | 3 ventanas distintas (30d fijo / todo-historial / per-producto) | 1 selector global → menu eng + rotación | Pricing queda exento (es rezago per-producto, no ventana) |
| Menu engineering | 422 silencioso (limit 500) → "no hay ventas" | limit 100 → datos reales | Arregla causa raíz de B1/B2 |
| Catálogo | solo Precio | + Costo, Te deja ($/%), Vendidos, buscador, filtros | Merge de 3 fuentes por product_id |
| Alta producto | nombre "a" válido, estación = Cocina auto | nombre ≥2 (no todo igual), estación obligatoria | B5/B4 |

---

## Mandatory Reading

| Priority | File | Lines | Why |
|---|---|---|---|
| P0 | `frontend/src/features/products/products-page.tsx` | 51-63, 180-204, 247-323 | Form (schema/defaults/select estación), montaje de bloques (268-275), tabla catálogo (277-323). Todo B1/B4/B5/B6/B7 pasa acá. |
| P0 | `frontend/src/features/products/menu-engineering-view.tsx` | 10, 25-36, 118-164 | `last30DaysIso()` local + `useProductPerformance({from, limit:500})` (**bug limit**) + tabla con Costo/Te deja/Vendidos (el shape que reusaremos en el catálogo). |
| P0 | `frontend/src/features/products/menu-engineering.ts` | 9-59 | `ClassifiedProduct` + `classifyMenu` (deriva unitPrice/unitCost del DTO). |
| P0 | `frontend/src/features/products/rotation-schedule.tsx` | 3, 10, 27-29 | `useProductRotation()` sin args → hay que pasarle `{from,to}`. |
| P0 | `frontend/src/features/products/pricing-inflation-card.tsx` | 10-21 | `usePricingInsights()` sin ventana → queda **exento** del período (es rezago per-producto). |
| P0 | `frontend/src/hooks/use-products.ts` | 7-10, 31-37 | `useProducts()` (base), `useProductRotation(query)` (acepta from/to). |
| P0 | `frontend/src/hooks/use-analytics.ts` | 30-36 | `useProductPerformance(query)` → `/analytics/products` (units_sold/food_cost/margin, ventana). |
| P0 | `frontend/src/hooks/use-inventory.ts` | 24 | `useFoodCost()` → `/inventory/food-cost`: costo+margen por producto **para todos los que tienen receta** (no depende de ventas). Fuente de "Costo"/"Te deja" del catálogo. |
| P0 | `frontend/src/lib/finance-range.ts` | 5-54 | `FinanceRange`, `FINANCE_RANGES`, `rangeWindow(range)` → `{from,to}` ISO. **Reusar** para el selector. |
| P1 | `frontend/src/api/types-operations.ts` | 20-30 | `ProductDTO` (+ `Station`). |
| P1 | `frontend/src/api/types-analytics.ts` | 28-42 | `ProductPerformanceRowDTO` + `AnalyticsQuery`. |
| P1 | `frontend/src/api/types-inventory.ts` | food-cost | `FoodCostRow`/`FoodCostResponse` (product_id, food_cost_amount, margin_amount, food_cost_ratio_bps, price_amount, currency). |
| P0 | `backend/app/presentation/schemas/products.py` | 8-13 | `CreateProductRequest` (name `min_length=1`, station default KITCHEN). B5/B4 backend. |
| P1 | `backend/app/application/product/use_cases.py` | 109-138 | `CreateProduct.execute` (no valida nombre). |
| P1 | `backend/app/domain/order/value_objects.py` | 35-39 | `Station` (KITCHEN/BAR). |

## Patterns to Mirror

### PERIOD_SELECTOR (mirror de Finanzas)
```tsx
// SOURCE: frontend/src/features/finance/finance-page.tsx (patrón) + lib/finance-range.ts:12-54
const [range, setRange] = useState<FinanceRange>("month")
const window = useMemo(() => rangeWindow(range), [range])
// UI:
{FINANCE_RANGES.map((r) => (
  <Button key={r.value} size="sm"
    variant={range === r.value ? "default" : "outline"}
    onClick={() => setRange(r.value)}>{r.label}</Button>
))}
```

### CLIENT_MERGE_BY_ID (para el catálogo B6)
```tsx
// products (base) + food-cost (costo/margen, todos con receta) + performance (vendidos, ventana)
const costById = new Map(foodCost.data?.rows.map((r) => [r.product_id, r]))
const soldById = new Map(perf.data?.map((r) => [r.product_id, r.units_sold]))
const rows = (products.data ?? []).map((p) => ({
  ...p,
  cost: costById.get(p.id)?.food_cost_amount ?? null,   // null → "—"
  margin: costById.get(p.id)?.margin_amount ?? null,
  marginBps: costById.get(p.id)?.food_cost_ratio_bps ?? null,
  units: soldById.get(p.id) ?? 0,
}))
```

### MONEY_FORMAT
```tsx
// SOURCE: products-page.tsx usa formatMoney(amount, currency) desde @/lib/money
formatMoney(p.price_amount, p.currency)
```

---

## Files to Change

| File | Action | Justification |
|---|---|---|
| `frontend/src/features/products/products-page.tsx` | UPDATE | Selector de período (B1); catálogo con columnas + buscador/filtros (B6/B7); estación obligatoria (B4). |
| `frontend/src/features/products/menu-engineering-view.tsx` | UPDATE | Recibir `window` por prop (en vez de `last30DaysIso`), `limit: 100` (arregla 422). |
| `frontend/src/features/products/rotation-schedule.tsx` | UPDATE | Recibir `window` por prop → `useProductRotation(window)`. |
| `frontend/src/features/products/product-catalog.tsx` | CREATE | Extraer la tabla del catálogo con columnas + filtros (mantiene `products-page` fino). |
| `frontend/src/features/products/product-catalog.ts` (+`.test.ts`) | CREATE | Helper puro `mergeCatalogRows()` + `filterCatalog(rows, {q, category, status})`. Testeable. |
| `frontend/src/hooks/use-inventory.ts` | UPDATE (si hace falta) | Confirmar/exponer `useFoodCost()` para el catálogo. |
| `backend/app/presentation/schemas/products.py` | UPDATE | `name` con validación (min 2, no todo el mismo carácter). |
| `backend/app/application/product/use_cases.py` | UPDATE (opcional) | Validación de nombre en el dominio/use case (defensa en profundidad). |
| `backend/tests/integration/test_e2e_products.py` | UPDATE | Test: nombre inválido → 422; alta ok. |
| `frontend/src/features/products/product-catalog.test.ts` | CREATE | Test de merge + filtros. |

## NOT Building
- ❌ Editar estación/categoría de productos existentes (retag de "todo Cocina") → necesita un endpoint de update de producto; va en **Fase 7 (ficha)**. Acá solo se **previene** en el alta.
- ❌ Limpieza de la fila basura "aaaaa" en la DB de prod → es dato (borrado manual/seed), no código. Se anota.
- ❌ Subir el cap de `/analytics/products` > 100 o paginarlo → se fija en 100 (alcanza para ≤100 productos); si un tenant supera 100, se resuelve en otra fase.
- ❌ Que "Precios vs inflación" siga el período global → es rezago per-producto, no ventana temporal. Queda exento (documentado).

---

## Step-by-Step Tasks

### Task 1 — Selector de período único (B1)
- **ACTION**: En `products-page.tsx`, agregar estado de período y los botones; pasar `window` a los bloques temporales.
- **IMPLEMENT**: `const [range, setRange] = useState<FinanceRange>("month"); const window = useMemo(() => rangeWindow(range), [range])`. Botones `FINANCE_RANGES` en el header. Pasar `<MenuEngineering window={window} />` y `<RotationSchedule window={window} />`. `PricingInflationCard` queda sin prop (exento).
- **MIRROR**: PERIOD_SELECTOR.
- **IMPORTS**: `import { FINANCE_RANGES, rangeWindow, type FinanceRange } from "@/lib/finance-range"`; `useState, useMemo`.
- **GOTCHA**: `rangeWindow` devuelve `{from,to}` ISO; `AnalyticsQuery` usa `from?/to?`. Compatibles.
- **VALIDATE**: `npm run build`; los 2 bloques cambian al togglear período.

### Task 2 — Arreglar menu engineering (limit + ventana) (B1/B2 causa raíz)
- **ACTION**: `menu-engineering-view.tsx` recibe `window: {from,to}` por prop; borrar `last30DaysIso()`; usar `limit: 100`.
- **IMPLEMENT**: `export function MenuEngineering({ window }: { window: { from: string; to: string } })` → `const query = useMemo(() => ({ from: window.from, to: window.to, limit: 100 }), [window])`.
- **GOTCHA**: el backend `/analytics/products` corta `limit` en `le=100` (`analytics.py:90`) → `limit:500` daba **422** y dejaba `perf.data` vacío (empty state "no hay ventas"). Bajar a 100 lo arregla. Confirmar en Network que ya no hay 422.
- **VALIDATE**: con ventas en el mes, la tabla y las 5 categorías se pueblan; sin 422.

### Task 3 — Rotación con el período global (B1)
- **ACTION**: `rotation-schedule.tsx` recibe `window` y lo pasa a `useProductRotation(window)`.
- **IMPLEMENT**: `export function RotationSchedule({ window }: {...})` → `useProductRotation({ from: window.from, to: window.to })`.
- **GOTCHA**: hoy `useProductRotation()` sin args agrega **todo el historial** por día de semana → de ahí "$15.894.600 sábado" (B2). Con ventana mensual, deja de sumar la historia entera.
- **VALIDATE**: la facturación por día baja a magnitudes del período elegido.

### Task 4 — Catálogo con Costo/Te deja/Vendidos (B6)
- **ACTION**: Crear `product-catalog.tsx` (tabla) + `product-catalog.ts` (helpers puros). Montar en `products-page` pasando `window`.
- **IMPLEMENT**:
  - Helper `mergeCatalogRows(products, foodCostRows, perfRows) -> CatalogRow[]` (CLIENT_MERGE_BY_ID).
  - Tabla con columnas: Nombre · Categoría · Estación · Precio · **Costo** · **Te deja ($ y %)** · **Vendidos** · Estado · Receta. Costo/margen `null` → "—". "Te deja %" = `100 - food_cost_ratio_bps/100` (o `margin/price`).
  - Datos: `useProducts()` + `useFoodCost()` + `useProductPerformance({...window, limit:100})`.
- **MIRROR**: la tabla de detalle de `menu-engineering-view.tsx:118-164` (mismas columnas Costo/Te deja/Vendidos).
- **GOTCHA**: food-cost trae solo productos **con receta**; el resto va "—" (aún no hay estado estimado/confirmado — eso es Fase 3). "Vendidos" es del período.
- **VALIDATE**: `npm run build`; un producto con receta muestra costo/margen; uno sin receta muestra "—".

### Task 5 — Buscador + filtros (B7)
- **ACTION**: En `product-catalog.tsx`, input de búsqueda + filtro por categoría + filtro por estado (activo/inactivo).
- **IMPLEMENT**: helper puro `filterCatalog(rows, { q, category, status })` (case-insensitive por nombre; categoría exacta; status). Estado local `useState`. Categorías derivadas de `products.data`.
- **VALIDATE**: buscar "napolitana" filtra; filtro categoría/estado funciona.

### Task 6 — Validación de nombre (B5) + estación obligatoria (B4)
- **ACTION (frontend)**: en `products-page.tsx` schema zod: `name` min 2 + refine "no todo el mismo carácter"; `station` sin preselección (placeholder) y requerido.
- **IMPLEMENT (frontend)**:
  ```tsx
  name: z.string().trim().min(2, "Mínimo 2 caracteres")
    .max(120)
    .refine((v) => new Set(v.replace(/\s/g, "")).size > 1, "Ingresá un nombre real"),
  station: z.enum(["KITCHEN", "BAR"], { required_error: "Elegí la estación" }),
  ```
  defaultValues: `station` → dejar sin setear (o `undefined`) y agregar `<option value="" disabled>Elegí…</option>` como primera opción del select.
- **ACTION (backend)**: en `schemas/products.py`, endurecer `name` (min 2 + validator anti-todo-igual) para que la API no dependa solo del front.
- **IMPLEMENT (backend)**:
  ```python
  from pydantic import field_validator
  name: str = Field(min_length=2, max_length=120)

  @field_validator("name")
  @classmethod
  def _real_name(cls, v: str) -> str:
      s = v.strip()
      if len(set(s.replace(" ", ""))) <= 1:
          raise ValueError("nombre inválido")
      return s
  ```
- **GOTCHA**: `Station` viene de `app.domain.order.value_objects` (no `product`). El default KITCHEN del schema/use case puede quedar (el form ahora siempre manda estación); lo que importa es que el **form** obligue a elegir.
- **VALIDATE**: back `poetry run pytest` (nombre "aa"/"aaaaa" → 422); front intenta crear sin estación → error.

### Task 7 — Tests
- **ACTION**: `product-catalog.test.ts` (merge + filtros); actualizar `test_e2e_products.py` (nombre inválido 422).
- **MIRROR**: `frontend/src/lib/finance-range.test.ts` (vitest, NOW fijo); `backend/tests/integration/test_e2e_preparations_api.py`.
- **GOTCHA**: `asyncio_mode=auto` (sin `@pytest.mark`).
- **VALIDATE**: `npm run test` + `poetry run pytest`.

---

## Testing Strategy

### Unit / helpers
| Test | Input | Expected |
|---|---|---|
| `mergeCatalogRows` | 1 producto con receta + 1 sin + perf de uno | costo/margen del 1º, "—" del 2º, units del que vendió |
| `filterCatalog` | q="nap", category, status | filtra por nombre/categoría/estado |
| backend name validator | "aa", "aaaaa", "  a ", "Milanesa" | 422, 422, 422, ok |

### Edge Cases
- [x] Período sin ventas → menu eng y rotación muestran su empty state (no 422, no contradicción).
- [x] Producto sin receta → Costo/Te deja "—" (no 0 engañoso).
- [x] Producto activo sin ventas en el período → Vendidos = 0.
- [x] Nombre con solo espacios / un carácter repetido → rechazado.
- [x] Tenant con >100 productos → menu eng limita a 100 (anotado como límite conocido).

---

## Validation Commands
```bash
cd backend && poetry run ruff check --fix && poetry run pytest      # sin regresiones (~400 tests)
cd frontend && npm run build && npm run test && npm run lint         # build = gate real
```
- **DB**: sin migración (`alembic upgrade head` = up to date).
- **Manual**: OWNER/`VITE_AUTH_BYPASS` → togglear período mueve menu eng + rotación juntos; catálogo con columnas + buscador; alta rechaza nombre corto y exige estación; Network sin 422 en `/analytics/products`.

---

## Acceptance Criteria
- [ ] Un solo selector de período gobierna menu engineering + rotación (Pricing exento, documentado).
- [ ] Sin 422 en `/analytics/products` (limit ≤100); menu engineering se puebla con ventas reales.
- [ ] Catálogo con Costo/Te deja ($ y %)/Vendidos + buscador + filtros.
- [ ] Alta valida nombre (≥2, no todo igual) y exige estación.
- [ ] Back + front verdes, sin migración.

## Risks
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| food-cost no cubre productos sin receta → columnas vacías confunden | M | Bajo | Mostrar "—" explícito; el estado estimado/confirmado llega en Fase 3 |
| Merge por product_id con datos desalineados de ventana | Baja | Bajo | Vendidos default 0; costo/margen independientes de la ventana |
| Cap 100 oculta productos en tenants grandes | Baja | Medio | Anotado; se resuelve al subir cap/paginar en fase posterior |

## Notes
- **Causa raíz B1/B2 identificada**: el "no hay ventas en 30 días" de menu engineering es (muy probablemente) un **422 enmascarado** por `limit=500`; y el "$15.894.600 sábado" es rotación sumando **todo el historial**. Ambos los cierra esta fase (limit→100 + ventana global). Verificar en Network al validar.
- **Retag de estaciones existentes** (agua/gaseosa/cafés en "Cocina") requiere editar productos → no hay endpoint de update de producto hoy; va en Fase 7. Acá se previene en el alta.
- **Fila basura "aaaaa"**: borrado de dato en prod, no código.
