# Implementation Report: Productos v3 — Fase 1 (Bugs P0)

## Summary
Se arreglaron los bugs visibles de `/app/products`: **selector de período único** que gobierna menu engineering + rotación (B1), con el fix de la **causa raíz** (menu engineering pedía `limit:500` y `/analytics/products` corta en `le=100` → 422 enmascarado que mostraba "no hay ventas" mientras rotación sí mostraba ventas del historial completo). Catálogo ampliado con **Costo / Te deja ($ y %) / Vendidos + buscador + filtros** (B6/B7). Validación de nombre (B5) y estación obligatoria (B4). Sin migraciones.

## Assessment vs Reality

| Metric | Predicted (Plan) | Actual |
|---|---|---|
| Complexity | Small–Medium | Small–Medium ✅ |
| Confidence | 8/10 | Implementado en una pasada, sin issues |
| Files Changed | ~10 | 8 (3 creados, 5 modificados) |

## Tasks Completed

| # | Task | Status | Notes |
|---|---|---|---|
| 1 | Selector de período único (B1) | ✅ | `useState<FinanceRange>` + `rangeWindow`, prop `period` a menu eng y rotación |
| 2 | Fix limit menu engineering (B1/B2) | ✅ | `limit:500→100` (elimina el 422); recibe `period` |
| 3 | Rotación con período global (B1) | ✅ | `useProductRotation({from,to})` |
| 4 | Catálogo Costo/Te deja/Vendidos (B6) | ✅ | Merge de products + food-cost + performance |
| 5 | Buscador + filtros (B7) | ✅ | Búsqueda por nombre + categoría + estado |
| 6 | Validación nombre (B5) + estación (B4) | ✅ | zod + pydantic `field_validator`; select con placeholder obligatorio |
| 7 | Tests | ✅ | 6 unit (catalog-rows) + 1 e2e (nombre inválido) |

## Validation Results

| Level | Status | Notes |
|---|---|---|
| Static Analysis | ✅ Pass | ruff limpio (back), eslint limpio (front), tsc vía build |
| Unit Tests | ✅ Pass | Front 143 (6 nuevos); back suite completa |
| Build | ✅ Pass | `npm run build` ok (247ms) |
| Integration | ✅ Pass | Backend e2e 409 tests verdes, sin regresiones |
| Edge Cases | ✅ Pass | Sin receta → "—"; nombre basura → 422; filtros |

## Files Changed

| File | Action | Notes |
|---|---|---|
| `frontend/src/features/products/catalog-rows.ts` | CREATED | Helpers puros: `mergeCatalogRows`, `filterCatalog`, `catalogCategories` |
| `frontend/src/features/products/catalog-rows.test.ts` | CREATED | 6 tests |
| `frontend/src/features/products/product-catalog.tsx` | CREATED | Tabla del catálogo + filtros + editor de receta (movido acá) |
| `frontend/src/features/products/products-page.tsx` | UPDATED | Fino: selector de período + form (validación/estación) + montaje de bloques |
| `frontend/src/features/products/menu-engineering-view.tsx` | UPDATED | Prop `period`, `limit:100`, texto de empty state |
| `frontend/src/features/products/rotation-schedule.tsx` | UPDATED | Prop `period` → `useProductRotation({from,to})` |
| `backend/app/presentation/schemas/products.py` | UPDATED | `name` min 2 + `field_validator` anti-basura |
| `backend/tests/integration/test_e2e_products_pricing.py` | UPDATED | `test_product_name_is_validated` |

## Deviations from Plan
- **Nombres de archivo**: el plan proponía `product-catalog.ts` (helpers) + `product-catalog.tsx` (componente); se usó **`catalog-rows.ts`** para los helpers para evitar la colisión de basename `.ts`/`.tsx` (imports ambiguos).
- **Editor de receta** (`RecipeForm`/`RecipeEditor`/`RecipeSheet`) se **movió** de `products-page.tsx` a `product-catalog.tsx` (pertenece a la fila del catálogo), evitando una dependencia circular entre ambos.
- Sin cambio en el use case de dominio para el nombre (la validación quedó en el schema Pydantic, que es el borde de la API); suficiente para B5.

## Issues Encountered
- Ninguno bloqueante. (El primer intento de correr pytest ejecutó en el dir del frontend por persistencia del `cd`; se repitió con el path correcto.)

## Tests Written

| Test File | Tests | Coverage |
|---|---|---|
| `frontend/.../catalog-rows.test.ts` | 6 | merge (con/sin receta), filtros (nombre/categoría/estado), categorías |
| `backend/.../test_e2e_products_pricing.py` | 1 | nombre inválido → 422, válido → 201 |

## Notas de alcance (diferido según plan)
- **Retag de estaciones existentes** (agua/gaseosa en "Cocina"): requiere endpoint de update de producto → **Fase 7 (ficha)**. Acá solo se previene en el alta.
- **Fila basura "aaaaa"** en prod: es dato, se limpia manual.
- **Precios vs inflación** queda exento del período global (es rezago per-producto, no ventana temporal).
- **Cap 100** en `/analytics/products`: alcanza para ≤100 productos; subir cap/paginar en fase posterior.

## Next Steps
- [ ] `/code-review` de los cambios
- [ ] `/prp-commit` + merge `--no-ff` a `main` (workflow del proyecto)
- [ ] Validación manual claro/oscuro + Network sin 422
