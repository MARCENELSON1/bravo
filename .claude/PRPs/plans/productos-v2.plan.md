# Plan: Productos v2 — menu engineering + precios/inflación + recetas madre

## Summary
Completar la Pantalla Productos al layout de los mockups. Es **XL** → se trocea en **3 tandas** por ROI: **A** menu engineering (reusa datos existentes, sin migración), **B** precios vs inflación + simulador + rotación por día (migración: histórico de precios + inflación), **C** recetas madre/anidadas (migración: sub-recetas multinivel + propagación de costo). Cada tanda: rama → validar → merge `--no-ff` → push.

## User Story
Como dueño, quiero ver mi carta clasificada (qué platos funcionan, cuáles me cuestan plata, cuáles nadie pide), saber si mis precios quedaron atrás de la inflación, y manejar preparaciones base que se propaguen a todos los platos — todo en pesos y con acciones.

## Metadata
- **Complexity**: XL (sliced en A/M, B/L, C/L)
- **Source**: research `wellnod-6-pantallas-cobertura.md` §4 + mockups Productos_01–11
- **Estimated Files**: A ~6 · B ~12 (+migr.0020) · C ~14 (+migr.0021)

## Contexto verificado del codebase
| Hecho | Detalle |
|---|---|
| **Receta = 1 nivel** | `RecipeORM` (1:1 con product, keyed `product_id`) + `RecipeItemORM` (ingredient+qty). **NO hay sub-recetas/recetas madre.** |
| Producto | `ProductORM`: `name, price_amount, category, station`. Frontend `products-page.tsx` (352 líneas) con `RecipeForm` (useRecipe/useSetRecipe). |
| **Performance por producto YA existe** | `ProductPerformanceRow{product_id, product_name, units_sold, sales_amount, food_cost_amount, margin_amount, currency}` vía `GetProductPerformance` (analytics) — expuesto en `product_margins` de `/finance/overview` y drill-down `/finance/products/{id}`. → **Tanda A reusa esto casi todo.** |
| Food cost hoy | `ProjectOrderSales` calcula `compute_food_cost(recipe.items, cost_by_ingredient)` al proyectar (un nivel). Tanda C debe extender esto a sub-recetas. |
| **NO existe** | histórico de cambios de precio (Tanda B), inflación (Tanda B), recetas anidadas (Tanda C). Última migración: `0019` → nuevas `0020+`. |
| Patrones | read model + use case + endpoint + container wiring (ver `finance_repo.py`/`analytics_repo.py`); frontend `GlassCard` + hooks + DTOs. |

---

## TANDA A — Menu engineering (quick-win, SIN migración)
**Entrega:** la carta clasificada en 5 categorías de acción, sobre el margen por producto que ya se calcula.
- **Backend:** reusar `GetProductPerformance` (ya da units/sales/food_cost/margin por producto). Evaluar un endpoint `GET /products/performance?from&to` que lo exponga directo (hoy solo sale dentro de `/finance/overview` top-10). Agregar `price_amount` y `unit_cost` (food_cost/units) al row si hace falta para "Precio/Costo/Te deja".
- **Lógica de categorías** (determinista, en el dominio o un helper): por **margen %** (margin/sales) y **volumen** (units vs promedio):
  - `no_vendido`: units == 0.
  - `revisar`: margen% < 45% (asesino de margen — vende pero deja poco).
  - `funciona`: margen alto + volumen alto.
  - `oportunidad`: margen alto + volumen bajo ("empujá estos").
  - `estable`: el resto ("tu base").
- **Frontend:** en `products-page.tsx` (o pantalla nueva) — hero con plata en juego, las 5 categorías (cards por grupo), tabla detalle (Precio/Costo/Te deja/Vendidos/Estado), top 3 que más dejan, asesinos de margen. Reusar `GlassCard`, `formatMoney`.
- **Tests:** unit de la clasificación (cada categoría); e2e del endpoint de performance.

## TANDA B — Precios vs inflación + simulador + rotación (migración 0020) — ✅ HECHA (`ec3b983`, 2026-08-02)
**Entrega:** "tus precios subieron X% vs inflación Y%", platos rezagados, simulador basado en histórico real, rotación por día de semana.
> Implementada. Inflación = un solo campo `advisor_settings.monthly_inflation_bps` (lo más liviano, no tabla de serie). Reporte: `reports/productos-v2-tanda-b-report.md`. Migración **0020** aplicada a dev. Solo queda **Tanda C**.
- **Backend:**
  - Tabla **`product_price_changes`** (tenant_id, product_id, old_price, new_price, changed_at) con **RLS** (migr. 0020). Registrar un cambio cada vez que se actualiza `price_amount` de un producto (hook en el use case de update de producto).
  - **Inflación:** tabla/config **`inflation_monthly`** (period, pct) cargable por el tenant o seed (INDEC) — o un campo simple en settings. Evaluar lo más liviano.
  - Read models: "días desde el último aumento" + "debería estar en $X" (precio × inflación acumulada desde el último cambio); simulador = mostrar el histórico real de cambios de ESE producto (no inventar elasticidad; si no hay historial, decirlo).
  - Rotación por día: agregación de `sale_facts` por `weekday × product` (heatmap Lun–Dom).
- **Frontend:** card "Precios vs inflación" (platos rezagados, simular/aplicar), simulador por producto, cronograma de rotación.
- **Tests:** unit del cálculo "debería estar en"; e2e del registro de cambio de precio + rotación por weekday.

## TANDA C — Recetas madre / anidadas (dominio nuevo; migración 0021) — PRÓXIMA, decisión de modelo FIJADA
**Entrega:** preparaciones base reutilizables con rendimiento; un cambio de costo de un insumo base se propaga a todos los platos.

### Decisión de modelo (fijada con el usuario 2026-08-02)
**Preparación base propia CON rendimiento** (elegida sobre "producto del catálogo usado como ingrediente"):
- Una **preparación** (receta madre) es una entidad NUEVA, separada del catálogo vendible: `name` + sus insumos + cuánto **rinde** (ej. "salsa fileto" rinde 2000 g).
- **Costo por unidad de la preparación** = costo total de sus insumos ÷ rendimiento. Un plato la referencia y usa X (ej. 150 g) → aporta `X × costo/unidad`.
- Ventaja: food cost exacto, no ensucia el catálogo. Costo: más migración/UX que la opción de reusar `product_id`.

### Motor actual confirmado (touchpoints — leído 2026-08-02)
| Pieza | Ubicación | Cómo se extiende |
|---|---|---|
| Cálculo puro | `domain/inventory/costing.py::food_cost(items, cost_by_ingredient, currency)` — Σ(qty × unit_cost)/1000, **matemática pura, sin I/O** | Extender a multinivel: un ítem puede ser insumo O preparación; el costo de una preparación se resuelve recursivamente con **guard anti-ciclo** (set de ids en la pila). |
| Entidades | `domain/inventory/recipe.py` (`Recipe{product_id, items}`, `RecipeItem{ingredient_id, qty}`) | `RecipeItem` pasa a poder apuntar a una preparación (`preparation_id` XOR `ingredient_id`). Nueva entidad `Preparation{id, name, yield_qty, items}`. |
| ORM | `RecipeORM` (1:1 product) + `RecipeItemORM` en `models.py` | Migr. **0021**: tablas nuevas `preparations` + `preparation_items` (RLS, patrón 0019) + columnas `sub_preparation_id` (nullable) en `recipe_items` **y** en `preparation_items` (una prep puede anidar otra prep → multinivel). `qty` en milésimas (mismo `QUANTITY_SCALE`). |
| Proyección food cost | `application/analytics/projection.py::ProjectOrderSales` (snapshot de food cost al pasar a PAID) | Usa la `food_cost` multinivel. **e2e de paridad**: una receta plana (solo insumos) debe dar EXACTAMENTE lo mismo que antes. |
| Read models que consumen food cost | `food_cost_repo.py` (`FoodCostReadModel`), `SqlAlchemyFinanceProductDetailReadModel` (drill-down), advisor | Deben resolver el costo multinivel al armar `cost_by_ingredient`/receta. |

- **Frontend:** sección "Recetas madre / preparaciones" (CRUD: nombre + insumos + rendimiento + "usada en N platos"); el editor de receta del producto (`RecipeForm` en `products-page.tsx`) suma la opción de agregar una preparación (además de insumos), con su cantidad.
- **Tests:** unit del food cost multinivel + **guard de ciclos** (A→B→A no cuelga); unit del prorrateo por rendimiento; **e2e de paridad** (receta plana = igual que hoy); e2e de propagación (cambiar costo de un insumo base → cambia el food cost de todos los platos que usan la preparación).
- **Sub-decisiones a resolver en implementación (menores):** unidad del rendimiento (¿libre por texto tipo "g/ml/u" o reusar la unidad del insumo principal?); si una preparación puede venderse como producto (por ahora: NO, son solo internas).

## NOT Building
- ❌ Carga de carta por foto/Excel con IA (integración pesada; fase futura).
- ❌ Sparklines de tendencia por producto (nice-to-have; se puede sumar en A/B).
- ❌ Fuente automática de inflación en vivo (Tanda B usa carga manual/seed, no scraping INDEC).

## Riesgos
| Risk | Prob | Impacto | Mitigación |
|---|---|---|---|
| Categorización "funciona/oportunidad" con umbrales arbitrarios | Media | Bajo | Umbrales explícitos y ajustables; determinista; el doc pide "estado accionable", no exactitud absoluta |
| Recetas anidadas rompen el food cost existente | Media | **Alto** | Tanda C aislada; guard anti-ciclo; e2e de paridad (receta plana da igual que antes); el motor de snapshots/sale_facts se re-testea |
| Inflación sin fuente confiable | Media | Medio | Carga manual por el tenant (MVP); no bloquear la card si falta el dato |
| Registrar price history retroactivo | Baja | Bajo | Empieza a registrar desde el deploy; "sin historial" se muestra honesto |

## Validación (por tanda)
```bash
cd backend && pytest
cd frontend && npm run lint && npm run test && npm run build
```
Migraciones de B/C: `alembic upgrade head` al dev DB; prod vía preDeploy Railway.

## Notes
- **Orden recomendado: A → B → C.** A es el quick-win (reusa `GetProductPerformance`, sin migración, mayormente frontend). B y C son features nuevas grandes con migración.
- Cada tanda es un plan de implementación de por sí; conviene `/prp-implement` una por una, no todas juntas.
- Tanda C es la más riesgosa (toca el cálculo de food cost que alimenta Finanzas) — hacerla con e2e de paridad y aislada.
- Reusar el estilo Wellnod (`GlassCard`, tokens, container `max-w-7xl`) y los patrones read-model/endpoint/hook ya establecidos en Finanzas.
