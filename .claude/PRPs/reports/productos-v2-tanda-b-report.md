# Implementation Report: Productos v2 — Tanda B (precios vs inflación + rotación)

**Fecha:** 2026-08-02 · **Rama:** `feat/productos-v2-b`

## Summary
Segunda tanda de Productos v2 (XL). Agrega el **histórico de precios por producto**,
el cálculo **"debería estar en $X"** según la inflación mensual estimada del tenant, un
**simulador** basado en el histórico real de cada plato, y la **rotación por día de
semana**. Migración **0020** (tabla nueva + columna aditiva). Queda pendiente la Tanda C
(recetas madre/anidadas, migración 0021).

## Assessment vs Reality
| Métrica | Plan | Real |
|---|---|---|
| Complejidad | L (+migr.0020) | L |
| Archivos | ~12 | 28 (17 mod + 11 nuevos) |
| Migración | 0020 | 0020 (product_price_changes RLS + advisor_settings.monthly_inflation_bps) |

## Decisiones de diseño
- **Fuente de inflación = lo más liviano** (el plan lo permitía): un solo campo
  `monthly_inflation_bps` en `advisor_settings` (reusa el endpoint `PUT /advisor/settings`
  y su form de costos), en vez de una tabla `inflation_monthly` con serie mensual. El
  dueño carga **una** estimación; "debería estar en" la compone sobre los meses (días/30)
  transcurridos desde el último cambio. Honesto como estimación.
- **No existía update de producto**: el catálogo solo tenía create/list. Se agregó el
  caso de uso `UpdateProductPrice` + `PUT /products/{id}/price` (que además registra el
  cambio). El **precio inicial se registra en `CreateProduct`** (baseline `old=None`), así
  cada producto nuevo tiene "días desde el último cambio" desde el día uno. Productos
  creados antes del deploy caen al `created_at` del producto (COALESCE en el read model).
- **Simulador = histórico real** (sin elasticidad inventada): cada fila rezagada se
  expande a su timeline real de precios + un editor precargado con el precio sugerido.
- **Rotación**: `EXTRACT(DOW)` de `sale_facts`, agrupado por (día, producto), plegado en
  Python a 7 filas Lun–Dom con unidades/ventas + plato estrella por día (UTC, MVP).

## Lo entregado (backend)
- Migración `0020_product_pricing`: tabla `product_price_changes` (RLS, patrón 0019) +
  columna `advisor_settings.monthly_inflation_bps` (patrón 0018). Aplicada al dev DB.
- `ProductPriceChangeORM`; `Product.change_price`; `AdvisorSettings.monthly_inflation_bps`.
- DTOs + ports + use cases en `application/product` (`suggested_price_amount` puro,
  `GetPricingInsights`, `UpdateProductPrice`, `GetProductPriceHistory`, `GetProductRotation`).
- Repos en `product_pricing_repo.py` (price-change repo + pricing read model + rotation).
- Endpoints en `/products`: `GET /pricing`, `GET /rotation`, `PUT /{id}/price`,
  `GET /{id}/price-history`. Inflación sumada al schema/endpoint/use case del asesor.
- Container: `price_change_repository`, `pricing_read_model`, `rotation_read_model` + 4
  use cases wired; `create_product` ahora recibe `price_changes`.

## Lo entregado (frontend)
- Tipos (pricing/histórico/rotación) + métodos en `products-api` + hooks
  (`usePricingInsights`, `useProductPriceHistory`, `useProductRotation`, `useUpdateProductPrice`).
- `pricing.ts` (helpers puros: `weekdayLabel`, `bpsToPct`, `pricingSummary`) + tests.
- `PricingInflationCard` (hero + rezagados + editor con histórico) y `RotationSchedule`
  (barras Lun–Dom + plato estrella), montados en `products-page` (grid 2 col).
- Input "Inflación mensual estimada (%)" en el form de costos del Asesor.

## Validación
| Check | Estado |
|---|---|
| Backend pytest | ✅ 385 (14 nuevos: 7 unit + 7 e2e) |
| Backend ruff | ✅ |
| Migración → dev | ✅ `alembic upgrade head` (0020) |
| Front build (tsc+vite) | ✅ |
| Front tests | ✅ 137 (5 nuevos) |
| Front lint | ✅ |

## Tests nuevos
- `tests/unit/test_pricing.py`: `suggested_price_amount` (sin inflación, 0 días, 1 mes,
  compuesto 2 meses, base 0) + `GetPricingInsights` con fakes (rezagado/ordenado/no configurado).
- `tests/integration/test_e2e_products_pricing.py`: baseline en create, log en update +
  reprice, no-op no logueado, rezagado con backdate (admin_engine), no-configurado,
  rotación por weekday, aislamiento multi-tenant (pricing + 404 de histórico cruzado).
- `pricing.test.ts`: weekday/bps/summary.

## Diferido / notas
- No hay serie mensual de inflación (una sola estimación); no hay scraping INDEC (plan lo excluye).
- Histórico de precios arranca en el deploy (sin retroactivo, por diseño).
- Rotación truncada en UTC (consistente con la serie diaria del MVP).
- **Pendiente: Tanda C** (recetas madre/anidadas, migración 0021 — la más riesgosa, toca
  el motor de food cost de Finanzas).

## Next Steps
- [ ] Revisión visual claro/oscuro en el navegador.
- [ ] Prod: la migración 0020 corre sola en el preDeploy de Railway.
- [ ] Tanda C en sesión nueva.
