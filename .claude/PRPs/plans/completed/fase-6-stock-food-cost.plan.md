# Plan: Fase 6 — Stock + Food cost (Inventory / Recipe / Supplier)

## Summary
Controlar **inventario** y **costo de mercadería** sobre la Clean Arch + multi-tenant ya existentes. Modela **insumos** (`Ingredient`), **proveedores** (`Supplier`) y **recetas opt-in** (`Recipe` que liga un `Product` a sus insumos). Vender un plato con receta **descuenta stock** y **dispara alerta de quiebre** al mínimo; cada producto expone su **food cost** (Σ insumos × costo) y su **margen**. Habilita el food-cost/mermas reales para la Capa 2 (asesor). Prioridad PRD: *Should*.

> **DECISIONES DE ALCANCE (cerradas — no re-litigar):**
> 1. **Unidad base por insumo.** `UnitOfMeasure` (G, KG, ML, L, UNIT). El insumo define **su** unidad base; stock, receta y compra se expresan en esa unidad. **Sin conversión automática** entre unidades (kg↔g diferido).
> 2. **Costo por insumo = `unit_cost` (`Money` por unidad base).** Se actualiza con cada compra (**último costo**; promedio ponderado diferido). Food cost de un producto = Σ(`recipe_qty` × `unit_cost`).
> 3. **Receta opt-in por producto.** Un `Product` **puede** tener `Recipe` o no. Sin receta → no descuenta stock (ej. bebidas compradas hechas). La receta no se inventa: la carga el OWNER/MANAGER.
> 4. **Descuento al vender (comanda → PAID).** Al conciliar la comanda a PAID, por cada ítem cuyo producto tiene receta se descuenta stock (`StockMovement` OUT `SALE`) y se evalúa quiebre. **Idempotente** (no descontar dos veces la misma comanda: guard por `order_id`). Consumo a tiempo de preparación = diferido.
> 5. **La venta NUNCA se frena por falta de stock.** Vender no valida disponibilidad; el stock puede quedar **negativo** (refleja realidad) y dispara alerta. No bloquear ventas reales por un insumo mal cargado.
> 6. **Alertas de quiebre** = insumos con `stock_qty ≤ min_qty`. Endpoint + indicador en la UI. **Sin push/WhatsApp** (lo toma la Capa 2 / Fase 10).
> 7. **Mermas** = `StockMovement` OUT `WASTE` (registro manual). **Compras** = `StockMovement` IN `PURCHASE` + actualiza `unit_cost`. El **link compra↔egreso** (Fase 3 OUTFLOW) queda **diferido** (MVP: inventario solo).
> 8. **Timestamps de servidor**, `Money` para costos (entero + moneda del tenant), multi-tenant + RLS en todo.

## Estado de implementación
PENDIENTE. Depende de Fase 2 (`Product`, `Order`, `OrderItem`) y se engancha con Fase 3 (settle a PAID) — ✅ ambas en `main`. Se implementa en rama `feat/fase-6-stock-food-cost`. Roadmap: tras Stock, Fase 7 (Reservas); Fase 8 (modelo canónico) puede arrancar en paralelo.

## User Story
Como **dueño/encargado** quiero **cargar insumos, proveedores y recetas** y que **vender descuente stock** para **saber qué tengo, qué me cuesta cada plato y cuándo reponer** sin planillas.

## Problem → Solution
Hoy no hay control de inventario ni costo de mercadería. → `Ingredient`/`Supplier`/`Recipe` con stock por movimientos; la comanda PAID dispara el consumo (receta → `StockMovement` OUT) y la evaluación de quiebre; el food cost y el margen por producto se derivan de receta × costo; las **mermas** y **compras** son movimientos manuales. Todo scoped por `tenant_id` + RLS.

---

## Modelo de dominio (nuevo: `inventory`)
- **`Ingredient`** (insumo): `id, tenant_id, name, unit (UnitOfMeasure), stock_qty (Decimal/int en milésimas de unidad base), min_qty, unit_cost (Money por unidad base), active, created_at`. Métodos: `apply(movement)` (suma/resta `stock_qty` según dirección), `set_cost(unit_cost)`. Propiedad `is_below_min`.
- **`StockMovement`**: `id, tenant_id, ingredient_id, direction (IN/OUT), reason (PURCHASE/SALE/WASTE/ADJUSTMENT), qty, order_id|None (set en SALE), unit_cost|None (set en PURCHASE), note|None, created_at`.
- **`Supplier`**: `id, tenant_id, name, contact|None, active, created_at`.
- **`Recipe`** (agregado, 1:1 con `Product`, opt-in): `product_id, tenant_id, items: list[RecipeItem]`. **`RecipeItem`**: `ingredient_id, qty (por unidad vendida)`.
- **VOs:**
  - `UnitOfMeasure` (StrEnum): `G, KG, ML, L, UNIT`.
  - `MovementDirection` (StrEnum): `IN, OUT`. `MovementReason` (StrEnum): `PURCHASE, SALE, WASTE, ADJUSTMENT`.
- **Cantidades:** enteros en **milésimas de la unidad base** (mismo criterio que `Money`: nada de float). Helper VO `Quantity` o int directo (a decidir en T1; recomendado int + factor 1000 documentado).
- **Funciones puras (testeables, estilo `taxation.py`/`hours.py`):**
  - `food_cost(items: list[RecipeItem], cost_by_ingredient: dict[str, Money]) -> Money`.
  - `margin(price: Money, food_cost: Money) -> Money` y `food_cost_ratio` (bps).
  - `is_below_min(stock_qty: int, min_qty: int) -> bool`.
- **Excepciones:** `IngredientNotFound`, `SupplierNotFound`, `RecipeNotFound`, `InvalidQuantity`, `InvalidUnitCost` (todas con `code` EN + `message` ES).
- **Ports:** `IngredientRepository`, `SupplierRepository`, `RecipeRepository`, `StockMovementRepository` (o un `InventoryRepository` agregado). `FoodCostReadModel` (margen por producto).

## Consumo por venta (cross-aggregate)
- Caso de uso **`ConsumeRecipesForOrder`**: dado `order_id`, si **no** hubo ya movimientos `SALE` para ese order (idempotencia), por cada `OrderItem` con receta descuenta `qty_item × recipe_qty` de cada insumo (`StockMovement` OUT `SALE`, `order_id` set) y evalúa quiebre.
- **Enganche:** se invoca cuando la comanda pasa a **PAID**. El settle de pagos (`_settle_order` / `RegisterPayment` en `application/payment/use_cases.py`) gana un **colaborador opcional inyectado** (port `InventoryConsumer`) que se llama tras `mark_paid()`. En tests se overridea con un fake/no-op. **No** acoplar dominios: el pago depende de un **port**, no de `inventory`.

## Read model / Food cost
- **`FoodCostReadModel`** (molde = `SqlAlchemyStaffReportReadModel`/`dashboard_repo`): por producto con receta devuelve `food_cost`, `price`, `margin`, `food_cost_ratio_bps`. Scoped por tenant + RLS.
- **Alertas:** `ListLowStock` → insumos con `stock_qty ≤ min_qty`.

## Config
- (Opcional) `low_stock_default_min` por tenant — **diferido**; el `min_qty` se setea por insumo.

---

## Mandatory Reading (moldes ya en el repo)
- **Fase 3 (pagos / settle):** `application/payment/use_cases.py` (`_settle_order`, `RegisterPayment`) → punto de enganche del consumo; `domain/payment/{entities,repository}.py`.
- **Fase 2 (catálogo):** `domain/product/entities.py`, `application/product/use_cases.py`, `presentation/api/v1/products.py` → molde de CRUD + RBAC; `Order/OrderItem` para el consumo.
- **Fase 5 (read model + persistencia + migración RLS):** `application/reporting/staff.py` + `infrastructure/persistence/staff_report_repo.py`; `alembic/versions/0006_shifts.py`/`0007_presence.py` (ENABLE/FORCE RLS + policy `tenant_isolation`); `models.py`, `mappers.py`, `shift_repo.py`.
- **Money / cantidades enteras:** `domain/shared/money.py`.
- **DI + Selector + errores + router:** `container.py`, `presentation/errors.py`, `main.py`, `presentation/rbac.py`.
- **Frontend:** `api/payments-api.ts` + `hooks/use-payments.ts`, `features/expenses/expenses-page.tsx` (tabla + sheet de alta), `features/products/products-page.tsx` (editor anidado para la receta), `components/shell/nav-config.ts`, `app/router.tsx`, `services/services-{context,provider}`, `test/test-utils.tsx`.

## Files to Change (orientativo)
**Backend (nuevos):** `domain/inventory/{entities,value_objects,exceptions,repository,recipe,costing.py}`, `application/inventory/use_cases.py`, `application/inventory/consume.py`, `application/inventory/ports.py` (`InventoryConsumer`), `infrastructure/persistence/{ingredient_repo,supplier_repo,recipe_repo,stock_movement_repo,food_cost_repo}.py`, `infrastructure/inventory/order_consumer.py` (adapter del port), `presentation/api/v1/inventory.py`, `presentation/schemas/inventory.py`, `alembic/versions/0008_inventory.py`, tests unit + e2e.
**Backend (editar):** `models.py`, `mappers.py`, `container.py`, `presentation/errors.py`, `main.py`, `application/payment/use_cases.py` (inyectar `InventoryConsumer` opcional + llamarlo en el settle), `tests/integration/conftest.py` (`_TABLES`).
**Frontend (nuevos):** `api/inventory-api.ts`, `api/types-inventory.ts`, `hooks/use-inventory.ts`, `features/inventory/{stock-page,suppliers-page}.tsx`, editor de receta (en producto).
**Frontend (editar):** `nav-config.ts` (grupo "Stock"), `app/router.tsx`, `services/services-{context,provider}`, `test/test-utils.tsx`, `features/products/products-page.tsx` (receta opt-in).

---

## Step-by-Step Tasks

### T1 — Dominio inventory
- `Ingredient`, `StockMovement`, `Supplier`, `Recipe`/`RecipeItem`; VOs (`UnitOfMeasure`, `MovementDirection`, `MovementReason`); `costing.py` (`food_cost`, `margin`, `is_below_min`); excepciones; ports.
- **Tests unit:** `apply` suma/resta stock, `food_cost` (2 insumos), `margin`, `is_below_min` (≤ límite), `InvalidQuantity` en qty ≤ 0.
- **MIRROR:** `domain/payment/entities.py`, `domain/invoice/taxation.py`, `domain/timeclock/hours.py`.

### T2 — Persistencia + migración RLS
- ORM `ingredients`, `suppliers`, `recipes`, `recipe_items`, `stock_movements` + mappers + repos. **Migración `0008_inventory`** (down_revision `0007_presence`): create + GRANT + ENABLE/FORCE RLS + policy `tenant_isolation` en cada tabla. `conftest._TABLES` ← prepend las nuevas.
- **MIRROR:** `0007_presence.py`, `models.py`, `mappers.py`, `payment_repo.py`/`shift_repo.py`.

### T3 — CRUD + API + RBAC
- Use cases: `CreateIngredient/ListIngredients/UpdateIngredient`, `CreateSupplier/ListSuppliers`, `SetRecipe/GetRecipe` (opt-in por producto), `RegisterPurchase` (IN + actualiza `unit_cost`), `RegisterWaste` (OUT WASTE), `ListLowStock`. Router `/inventory/*` (OWNER/MANAGER) + `/products/{id}/recipe`. Container + `errors.py` + `main.py`.
- **Tests e2e:** alta insumo/proveedor; compra sube stock + costo; merma baja stock; alerta cuando ≤ min; RLS.
- **MIRROR:** `application/payment/use_cases.py`, `presentation/api/v1/{payments,products}.py`, `rbac.py`.

### T4 — Consumo por venta + food cost
- `InventoryConsumer` port + `OrderInventoryConsumer` adapter; `ConsumeRecipesForOrder` (idempotente por `order_id`). Inyectar el port en el settle de pagos y llamarlo al pasar a PAID. `FoodCostReadModel` + `GET /inventory/food-cost`.
- **Tests e2e:** comanda con producto+receta → PAID descuenta stock y dispara alerta; re-conciliar **no** vuelve a descontar (idempotencia); food cost/margen correctos; venta sin receta no toca stock.
- **MIRROR:** `application/reporting/staff.py`, `infrastructure/persistence/staff_report_repo.py`, `_settle_order`.

### T5 — Frontend
- `InventoryApi` + `use-inventory` hooks; registrar en `services-{context,provider}` + `test-utils`.
- Página **Stock** (insumos: stock, mín, costo, alerta; compras; mermas), página **Proveedores**, **editor de receta** en el producto (opt-in), vista de **food cost/margen**. Nav grupo "Stock" + rutas (OWNER/MANAGER).
- **Validar:** tsc + eslint + vitest + build.
- **MIRROR:** `hooks/use-payments.ts`, `features/expenses/expenses-page.tsx`, `features/products/products-page.tsx`, `features/timeclock/staff-page.tsx`.

---

## Validation Commands
- **Backend:** `poetry run ruff check app tests` · `poetry run mypy app` · `poetry run pytest -q` (cobertura ≥ 80% en domain/application).
- **Frontend:** `npx tsc --noEmit` · `npx eslint src` · `npx vitest run` · `npx vite build`.

## Acceptance Criteria
- Cargar insumo/proveedor; **compra** sube stock y actualiza costo; **merma** baja stock.
- Producto con **receta opt-in**; vender (comanda PAID) **descuenta** los insumos de la receta y, si llega al mínimo, aparece en **alertas**. Re-conciliar no descuenta dos veces.
- La venta **no se bloquea** por falta de stock (puede quedar negativo + alerta).
- **Food cost y margen** por producto correctos (Σ insumos × costo).
- Scoped por tenant (RLS). ruff + mypy + pytest + tsc + eslint + vitest + build en verde.

## Complexity / Confidence
- **Complejidad:** Media-alta. T1–T3 son CRUD sobre patrones probados (alto reuso). T4 (consumo por venta + idempotencia + enganche al settle de pagos sin acoplar dominios) es la parte fina. Cantidades enteras (milésimas) + food cost en `Money` requieren cuidado pero hay molde (`Money`).
- **Confianza:** Alta en T1–T3 y T5. Media en T4 (cross-aggregate idempotente detrás de un port).

## Out of scope (diferido)
- Conversión entre unidades (kg↔g); promedio ponderado de costo (hoy último costo); consumo a tiempo de preparación (hoy al vender/PAID); link compra↔egreso (Fase 3); órdenes de compra / recepción parcial; lotes/vencimientos; conteo físico/ajuste por inventario cíclico; alertas push/WhatsApp (Capa 2); food cost teórico vs real (mermas) como KPI del asesor (Fase 9).
