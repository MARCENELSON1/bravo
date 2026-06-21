# Implementation Report: Fase 6 — Stock + Food cost (Inventory / Recipe / Supplier)

## Summary
Inventario y costo de mercadería sobre la Clean Arch + multi-tenant existentes. Nuevo dominio `inventory`:
insumos (`Ingredient`), proveedores (`Supplier`), recetas opt-in por producto (`Recipe`), y movimientos de
stock (`StockMovement`). Vender una comanda (→ PAID) descuenta los insumos de la receta (idempotente, detrás de
un port `InventoryConsumer` enganchado al settle de pagos, sin acoplar dominios) y dispara alerta de quiebre al
mínimo. Cada producto expone su food cost (Σ insumos × costo), margen y ratio. Frontend: páginas Stock /
Proveedores, editor de receta dentro de Productos, y vista de food cost.

## Assessment vs Reality

| Metric | Predicted (Plan) | Actual |
|---|---|---|
| Complexity | Media-alta (T4 la parte fina) | Coincide — T4 (cross-aggregate idempotente) fue lo más delicado |
| Confidence | Alta T1–T3/T5, Media T4 | Confirmado; T4 salió limpio con guard `exists_for_order` |
| Files Changed | ~30 nuevos/editados | 45 archivos (3570+ líneas) |

## Tasks Completed

| # | Task | Status | Notes |
|---|---|---|---|
| T1 | Dominio inventory | ✅ Complete | Entities, VOs, costing puro, ports, excepciones; 15 tests |
| T2 | Persistencia + migración RLS | ✅ Complete | ORM + mappers + 4 repos + migración 0008 (RLS) reversible |
| T3 | CRUD + API + RBAC | ✅ Complete | /inventory/* + /products/{id}/recipe; 13 e2e |
| T4 | Consumo por venta + food cost | ✅ Complete | InventoryConsumer port + ConsumeRecipesForOrder + FoodCostReadModel; 4 e2e |
| T5 | Frontend | ✅ Complete | Stock/Proveedores/Receta/Food cost; 10 tests |

## Validation Results

| Level | Status | Notes |
|---|---|---|
| Static Analysis | ✅ Pass | ruff + mypy (195 archivos) limpios; tsc + eslint limpios |
| Unit Tests | ✅ Pass | 15 unit dominio inventory + 4 lib frontend |
| Build | ✅ Pass | `vite build` ok (warning de chunk preexistente) |
| Integration (e2e) | ✅ Pass | 17 e2e backend (13 inventory + 4 food cost) + 6 api frontend |
| Edge Cases | ✅ Pass | stock negativo, idempotencia re-settle, venta sin receta, RLS, 404s |
| Coverage | ✅ Pass | inventory dominio+aplicación 92% (≥80% requerido) |

## Files Changed (45)
**Backend nuevos:** `domain/inventory/{__init__,value_objects,exceptions,recipe,entities,costing,repository}.py`;
`application/inventory/{__init__,use_cases,ports,consume,food_cost}.py`;
`infrastructure/persistence/{ingredient_repo,supplier_repo,recipe_repo,stock_movement_repo,food_cost_repo}.py`;
`presentation/api/v1/inventory.py`;
`presentation/schemas/inventory.py`; `alembic/versions/0008_inventory.py`;
`tests/unit/test_inventory.py`, `tests/integration/test_e2e_inventory.py`, `tests/integration/test_e2e_food_cost.py`.
**Backend editados:** `models.py`, `mappers.py`, `container.py`, `main.py`, `presentation/errors.py`,
`application/payment/use_cases.py`, `tests/integration/conftest.py`.
**Frontend nuevos:** `api/{types-inventory,inventory-api,inventory-api.test}.ts`, `hooks/use-inventory.ts`,
`lib/{inventory,inventory.test}.ts`, `features/inventory/{stock-page,suppliers-page}.tsx`.
**Frontend editados:** `services/services-{context,provider}.tsx`, `test/test-utils.tsx`,
`features/products/products-page.tsx`, `components/shell/nav-config.ts`, `app/router.tsx`.

## Deviations from Plan
1. **Sin adapter de infraestructura para el consumo.** El plan listaba `infrastructure/inventory/order_consumer.py`.
   En su lugar `ConsumeRecipesForOrder` (application) **implementa** el port `InventoryConsumer` directamente: el
   consumo es lógica de negocio (orquesta repos de dominio), no un servicio externo, así que no requiere un adapter
   en infra. El pago sigue dependiendo del **port**, no de inventory.
2. **`food_cost(...)` lleva parámetro `currency`.** Money siempre necesita una moneda (incluso receta vacía / costo
   faltante); el plan no lo incluía en la firma.
3. **`margin(...)` devuelve `int` (no `Money`).** El margen puede ser **negativo** (venta bajo costo) y Money no
   admite negativos; una herramienta de food cost debe mostrar la pérdida, no ocultarla.
4. **Receta persistida en tabla relacional** `recipes` (PK `product_id`) + `recipe_items` (sin identidad de dominio;
   el repo los reemplaza con uuid al guardar), como indicaba el plan.
5. **Endpoints de receta bajo `/products/{id}/recipe`** (no `/inventory/...`) para el editor dentro del producto.

## Issues Encountered
- **mypy: `list` como nombre de método** sombreaba el builtin → `list[Ingredient]` en un método posterior fallaba.
  Resuelto reordenando `list_below_min` antes de `list` en `IngredientRepository` (igual que `ShiftRepository`).
- **Orden de providers en el container:** el settle de pagos inyecta `InventoryConsumer`, así que los repos de
  inventario + `consume_recipes_for_order` se definen **antes** de la sección de pagos.
- **ruff import-order** en la migración (auto-fix), como en 0006/0007.

## Tests Written

| Test File | Tests | Coverage |
|---|---|---|
| `tests/unit/test_inventory.py` | 15 | entities (apply/set_cost), costing (food_cost/margin/ratio/is_below_min), VOs |
| `tests/integration/test_e2e_inventory.py` | 13 | CRUD, compra/merma, alerta, receta opt-in, RLS, 404s |
| `tests/integration/test_e2e_food_cost.py` | 4 | consumo en PAID + alerta, idempotencia re-settle, venta sin receta, food cost/margen |
| `frontend/src/api/inventory-api.test.ts` | 6 | métodos del cliente (POST/PUT/GET + body) |
| `frontend/src/lib/inventory.test.ts` | 4 | formatQty / toMilesimas / formatBps |

## Next Steps
- [ ] Code review via `/code-review`
- [ ] Merge a `main` (rama `feat/fase-6-stock-food-cost`)
- [ ] Validación en vivo: cargar insumos/recetas en un tenant real y confirmar descuento al cobrar
- [ ] Fase 7 (Reservas) — siguiente en el roadmap
