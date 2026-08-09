# Plan: Productos v3 — Fase 2, Tanda B (IVA neto)

## Summary
Costear **neto de IVA**: el proveedor factura con o sin IVA y el precio de la carta lo incluye; si se mezclan, el margen se va ~21% de lado. Se guarda el costo del insumo **neto**, se netea el precio de venta para calcular margen, y se **muestra con IVA** al dueño (el número que conoce). Tasa de IVA global configurable (default 21%, patrón de `monthly_inflation_bps`), reusando `split_vat()` del dominio de facturación. Migración 0023.

> ⚠️ **A diferencia de la merma (2A), esto CAMBIA números de Finanzas ya en prod**: el margen pasa a calcularse sobre neto. No es no-op. Es una **corrección deliberada** (el margen actual está inflado por IVA). Ver "Decisión abierta".

## User Story
Como **dueño**, quiero que **el margen se calcule neteando el IVA de costos y precios**, para que **el "te deja $X" sea real y no esté inflado por el impuesto**.

## Problem → Solution
Hoy `unit_cost` (insumo) y `price` (producto) son brutos y se restan tal cual → margen mezcla IVA. Solución: **todo neto internamente** (costo del insumo neto; precio neteado para margen), **bruto en la UI**.

## Metadata
- **Complexity**: Medium-Large (~12 archivos, toca costos Y precios)
- **Source PRD**: `productos-v3.prd.md` — Fase 2 (Ticket 1.3)
- **PRD Phase**: 2 (Tanda B de 4). Depende conceptualmente de 2A (merma) ya en `main`.
- **Migración**: **0023** (add `advisor_settings.default_vat_bps` + `stock_movements.price_includes_tax`/columna de tasa si se guarda histórico).

---

## Lo que define el spec (Ticket 1.3) — sin decisiones abiertas

Textual: *"TODO se guarda neto de IVA. En la carga de compra hay un check 'el precio incluye IVA' y se netea al guardar. El precio de venta también se netea para calcular margen, y se muestra con IVA al dueño. Documentar esto en la UI con una línea."*

De ahí se sigue, **sin inventar nada**:
- **Tasa global**, default **21%** (`default_vat_bps = 2100`). El spec no pide tasa por ítem; las constantes VAT_21/VAT_105 del dominio de facturación son el estándar → 21% por default, editable como la inflación.
- **Check "el precio incluye IVA"** en la carga de compra (default **True**; los precios de lista AR suelen venir con IVA). Si está tildado, se netea al guardar.
- **Se aplica** (el spec dice "TODO se guarda neto"). **Sin flag de opt-in ni tasa por ítem** — eso no está en el spec; queda como posible futuro solo si el dueño reporta mezcla real de tasas.
- **UI: mostrar con IVA + una línea aclaratoria** ("Margen neto de IVA").

---

## Mandatory Reading

| Priority | File | Why |
|---|---|---|
| P0 | `backend/app/domain/invoice/taxation.py` | `split_vat(total, rate_bp)` → `net = round(total*10000/(10000+rate))`. **Reusar** para netear (no reimplementar). |
| P0 | `backend/app/domain/invoice/value_objects.py` (VAT_21=2100…) | Constantes de tasa en bps. |
| P0 | `backend/app/domain/inventory/costing.py` | `margin()` = price − food_cost (ambos Money). Acá se netea el price antes de `margin`/`food_cost_ratio_bps`. Es el punto donde el neteo del precio entra sin romper `food_cost()`. |
| P0 | `backend/app/application/inventory/use_cases.py` | `RegisterPurchase` / `CreateIngredient` (netear `unit_cost_amount` en la carga si `price_includes_tax`). |
| P0 | `backend/app/domain/advisor/entities.py` + `models.py AdvisorSettingsORM` | Patrón `monthly_inflation_bps` (add `default_vat_bps`). |
| P0 | `backend/app/infrastructure/persistence/food_cost_repo.py` | Netear el `price` del producto antes de `margin`/`ratio` (el food_cost ya vendrá neto porque el costo del insumo se guarda neto). |
| P0 | `backend/app/application/analytics/projection.py` | El `food_cost_amount` en `sale_facts` ya será neto (costo neto). Confirmar que el margen/advisor que lee sale_facts sea coherente. |
| P0 | `backend/app/application/advisor/report.py` | El motor del Asesor computa márgenes desde sale_facts/precios. Si el precio se netea acá también, revisar que no se doble-netee. **Punto de mayor riesgo de doble-conteo.** |
| P1 | `backend/app/presentation/schemas/inventory.py` (`PurchaseRequest`, `CreateIngredientRequest`) | Add `price_includes_tax: bool = True`. |
| P1 | `backend/alembic/versions/0022_ingredient_yield.py` | Patrón de migración add-column. Última = **0022**; nueva = `0023_default_vat`. |
| P1 | Frontend: form de compra/insumo (`stock-page.tsx`) + input de tasa en Asesor (`advisor-page`) | Check "el precio incluye IVA" + campo de tasa global. Mostrar precios con IVA + una línea aclaratoria. |

## Approach (resumen técnico)

1. **Costo del insumo neto**: en `CreateIngredient`/`RegisterPurchase`, si `price_includes_tax`, `unit_cost_amount = split_vat(Money(amount), default_vat_bps).net`. Guardar neto. (El histórico en `stock_movements` guarda lo cargado + el flag.)
2. **Precio neto para margen**: en el read model de food-cost y donde se calcule margen, netear el precio: `net_price = split_vat(price, default_vat_bps).net`; `margin = net_price − food_cost` (food_cost ya neto).
3. **UI bruto**: el catálogo y las fichas muestran el precio **con IVA** (como hoy, sin cambio de dato); solo el **margen** cambia (ahora neto). Una línea: "Margen neto de IVA".
4. **Tasa global**: `advisor_settings.default_vat_bps` (default 2100), editable en el Asesor, igual que la inflación.
5. **NO tocar `food_cost()`/`split_vat()`**: se reusan; el neteo entra en los bordes (carga + cálculo de margen), como la merma.

## NOT Building
- ❌ Tasa por ítem (Opción B) — futuro si hay mezcla real.
- ❌ Discriminar IVA en el reporte del contador (eso ya sale de comprobantes AFIP reales, ver plan `reportes-fase-10`).
- ❌ Re-netear `sale_facts` históricos (el snapshot es al momento de venta; aplica de acá en más).

## Testing Strategy (clave: NO paridad — cambia a propósito)
| Test | Expected |
|---|---|
| unit: costo con `price_includes_tax` | se guarda neto (1210 con 21% → 1000) |
| unit: margen neteado | net_price − net_cost, no bruto − bruto |
| e2e: food-cost con IVA on | margen menor que con IVA off (corrección) |
| doble-neteo | el Asesor NO netea dos veces (food_cost neto + price neteado una vez) |

## Risks
| Risk | Impacto | Mitigation |
|---|---|---|
| **Doble neteo** (Asesor + food-cost ambos netean) | Alto | Un solo punto de neteo del precio; test explícito; trazar `report.py` |
| Cambia márgenes en prod sin aviso | Medio | Es corrección deliberada; comunicar; considerar flag de opt-in por tenant (`vat_netting_enabled`, default off → prender por tenant) para migración suave |
| Tasa global no cubre mezcla | Bajo | Opción B como futuro |

## Notes
- Reusa 100% `split_vat` + el patrón de campo global de la inflación (Tanda B). Sin `Decimal`/float.
- **Riesgo técnico #1 = doble/mal neteo**: el margen se calcula en dos motores — el read model de food-cost (`food_cost_repo.py`) y el Asesor (`advisor/report.py`, que resta `sale_facts.food_cost_amount` de `line_amount`). Al netear el costo del insumo, `food_cost_amount` ya queda neto; **hay que netear también el precio en AMBOS** (una sola vez cada uno), o el margen del Asesor queda con precio bruto − costo neto (inflado). Trazar `report.py`/`kpis.py` antes de tocar.

---

## Estado actual (rama `feat/productos-v3-fase-2b-iva`, SIN commitear) y cómo terminar

**Ya hecho en la rama** (validado verde, pero NO commiteado — ver hallazgos):
- `advisor_settings.default_vat_bps` (default **0 = off/paridad**), migración **0023**.
- `Ingredient.cost_includes_tax` (flag por-insumo), migración **0024**.
- `AdvisorKpis` netea ventas+food **por agregado** (tasa global); `food_cost_repo` netea **per-insumo** (respeta el flag); `net_effective_unit_cost` en `costing.py`; `net_of_vat` en `kpis.py`.
- Frontend: campo "IVA (%)" en el Asesor + checks "¿incluye IVA?" en alta/compra + tipos.
- Tests: unit de neteo (`test_advisor_vat.py`) + e2e monotributo.

**Code review xhigh (26 agentes) → 12 hallazgos, 5 correctness confirmados. NO es commit-ready:**
- **F1/F2/F7** — el flag `cost_includes_tax` se **pisa solo** al comprar (default `True` + checkbox tildado) y **no hay edición** (falta en `UpdateIngredient`). Data corruption silenciosa.
- **F3/F4/F5** — **inconsistencia neto/bruto**: Productos netea per-insumo, el Asesor por agregado (divergen en tenants mixtos); el catálogo muestra precio bruto + costo/margen neto (no cierra: Precio−Costo≠"Te deja"); el hero del Asesor muestra Ventas brutas + Margen neto (no cuadra).
- **F6** cache LLM sin `vat_bps` · **F10** duplicación de `net_of_vat` · **F9** ORM sin `server_default` · **F12** revision id ≠ filename · **F8** float rounding (menor, idioma consistente).

### Orden para la pasada fresca: (a) → (b) → (c)

**(a) Bugs del flag** (seguro, independiente — hacer primero):
- `PurchaseRequest.price_includes_tax: bool | None = None`; `RegisterPurchase` solo setea el flag si viene (no lo pisa).
- `PurchaseSheet`: sembrar el checkbox desde `ingredient.cost_includes_tax` + remontar al abrir (como `EditIngredientSheet`).
- `UpdateIngredientRequest` + `UpdateIngredient` + `EditIngredientSheet`: exponer `cost_includes_tax` (edición no-destructiva).
- `IngredientORM.cost_includes_tax`: agregar `server_default` (F9). Renombrar el archivo de migración 0024 para matchear el revision id (F12).

**(b) DECIDIR la regla de presentación** (el nudo — elegir UNA y aplicarla a Productos/Finanzas/Asesor):
- **B1** análisis todo neto (precio de carta "con IVA" como dato aparte).
- **B2 (recomendada):** precio/costo/ventas **brutos** + margen/"te deja" **netos** etiquetados "neto de IVA"; food cost % como ancla (invariante al IVA).
- **B3** doble columna bruto/neto.

**(c) Netear per-insumo en el Asesor** (consistencia con Productos, después de (b)):
- `ProjectOrderSales`: netear el costo per-insumo (`net_effective_unit_cost` con la tasa del tenant) → `sale_facts.food_cost` neto. Inyectar `AdvisorSettingsRepository` — **ojo: el provider `advisor_settings_repository` se define DESPUÉS de `project_order_sales` en `container.py`, moverlo antes.**
- `AdvisorKpis`: dejar de netear el food cost (ya viene neto de `sale_facts`); netear **solo** ventas. Revertir `_net_food_cost`.
- Al prender IVA: correr rebuild (`POST /analytics/rebuild` + snapshots) para que el histórico quede neto.
- Cleanup: F6 (`vat_bps` al fingerprint del cache), F10 (unificar `net_of_vat` en `domain/shared`).

Migraciones en la rama: **0023, 0024** (aplicadas a dev; `main` no las tiene). El IVA está **off por default**, así que nada en vivo se afecta hasta que se termine y prenda.
