# Plan: Fase 2 — Comandas + KDS

## Summary
Primer módulo del **motor operativo**: capturar la comanda digital (mozo) y mostrarla en cocina (KDS web, cuasi tiempo real por polling). Agrega el dominio `Table`/`Product`/`Order`/`OrderItem` sobre la Clean Arch + multi-tenant + RLS de la Fase 1, e **introduce el value object `Money`** (enteros en unidad mínima + ISO-4217) y la **config país/moneda del tenant** — infra compartida del resto del motor.

## User Story
Como **mozo (WAITER)** quiero **cargar la comanda de una mesa eligiendo productos y enviarla a cocina**, y como **cocina (KITCHEN)** quiero **ver las comandas entrantes en una pantalla que se actualiza sola y marcarlas en preparación/listas**, para que **el pedido fluya del salón a la cocina sin papel ni gritos**.

## Problem → Solution
Hoy no hay nada operativo (Fase 1 = solo identidad). → El local opera el ciclo **mesa → comanda → cocina (KDS) → servido**, con productos y precios en `Money`, todo tenant-scoped con RLS. Es la primera fuente de dato first-party (ventas/ítems) que después alimentará al asesor.

## Metadata
- **Complexity**: **XL** (módulo de dominio completo backend + KDS/mozo/admin frontend + nuevo VO transversal `Money` + migración con RLS). *Se puede partir en 2 commits/sub-rebanadas en el límite backend↔frontend (y opcionalmente catálogo↔comandas).* 
- **Source PRD**: `.claude/PRPs/prds/nucleo.prd.md`
- **PRD Phase**: Fase 2 — Comandas + KDS
- **Estimated Files**: ~45 (≈30 backend, ≈15 frontend)

---

## UX Design

### Before
```
Mozo anota en papel → camina a la cocina → grita/pega el ticket.
Cocina no tiene cola digital. Sin registro de qué se vendió.
```

### After
```
MOZO (rol WAITER)                         COCINA (rol KITCHEN)
/app/floor  → grilla de mesas             /app/kds  (board, refetch cada 5s)
  elegir mesa → /app/orders/:tableId       ┌───────────┬───────────┐
  buscar/elegir productos                  │ Mesa 5    │ Mesa 2    │
  + cantidad + nota → total en vivo        │ 2x Milanesa│ 1x Lomo   │
  [Enviar a cocina]  (OPEN→SENT)           │ [Preparar] │ [Listo]   │
                                           └───────────┴───────────┘
ADMIN (OWNER/MANAGER): /app/products → alta/edición de productos (precio en Money)
```

### Interaction Changes
| Touchpoint | Before | After | Notes |
|---|---|---|---|
| Cargar pedido | papel | comanda digital por mesa | rol WAITER |
| Cocina ve el pedido | ticket físico | KDS web, polling 5s | rol KITCHEN |
| Estado del pedido | — | OPEN→SENT→PREPARING→READY→SERVED (+CANCELLED) | máquina de estados en el dominio |
| Precios | — | `Money` (entero unidad mínima + ISO-4217), moneda del tenant | nunca float |

---

## Mandatory Reading

Leer ANTES de implementar. La Fase 1 es el molde exacto — **imitar estilo, nombres y estructura**.

### Backend — vertical slice (molde a copiar)
| Prio | File | Why |
|---|---|---|
| P0 | `backend/app/domain/user/entities.py` | Entidad dataclass (no frozen) con métodos de negocio/invariantes → molde para `Order` con lifecycle |
| P0 | `backend/app/domain/user/value_objects.py` | `Email` (frozen + `__post_init__` validación) y `Role` (StrEnum) → molde para `Money` y `OrderStatus` |
| P0 | `backend/app/domain/errors.py` + `backend/app/domain/user/exceptions.py` | `DomainError` base (code EN + message ES) → molde para excepciones de Order/Product |
| P0 | `backend/app/presentation/errors.py` | `_STATUS_BY_TYPE` (registrar nuevas excepciones → status) |
| P0 | `backend/app/domain/user/repository.py` | Port ABC async con `tenant_id` en cada método → molde para repos |
| P0 | `backend/app/application/identity/onboard_tenant.py` + `invite_user.py` | Use case: ctor inyecta ports, `async execute(*, ...)`, `tenant_context.set()`, `str(uuid4())`, levanta DomainError |
| P0 | `backend/app/application/identity/dtos.py` | DTOs `@dataclass(frozen=True)` input/output |
| P0 | `backend/app/presentation/api/v1/users.py` + `tenants.py` | Router `@inject` + `Depends(Provide[Container.x])`, `require_roles(...)`, `status_code` |
| P0 | `backend/app/presentation/schemas/users.py` | Pydantic `Field()` + `@field_validator` |
| P0 | `backend/app/presentation/deps.py` + `rbac.py` | `current_identity` → `AccessClaims(user_id, tenant_id, role)`; `require_roles(*roles)` |
| P0 | `backend/app/infrastructure/persistence/models.py` | ORM `Mapped[...]`, `Uuid(as_uuid=False)`, `tenant_id` FK+index, `server_default=func.now()` |
| P0 | `backend/app/infrastructure/persistence/mappers.py` | `*_to_domain` (incluye created_at) / `*_to_orm` (**omite created_at**) |
| P0 | `backend/app/infrastructure/persistence/user_repo.py` | Repo: `async with self._session_factory()`, filtro `tenant_id` explícito (defensa en profundidad), `add`=session.add, `save`=session.merge |
| P0 | `backend/app/infrastructure/persistence/database.py` + `app/context.py` | `SET LOCAL app.tenant_id` por transacción (`set_config(...,true)`) |
| P0 | `backend/alembic/versions/0001_initial.py` | Migración: `create_all`, `ENABLE`+`FORCE RLS`, **policy `tenant_isolation` con `current_setting('app.tenant_id', true)::uuid`** |
| P0 | `backend/app/container.py` | Wiring: `providers.Factory(Repo, session_factory=db.provided.session)` y `Factory(UseCase, dep=...)` |
| P1 | `backend/tests/fakes/__init__.py` | Fake repo in-memory (filtra `tenant_id`) + `Harness` (seed_tenant/seed_user, builders) |
| P1 | `backend/tests/unit/test_auth_core.py` | Unit test async con Harness+fakes |
| P1 | `backend/tests/integration/conftest.py` + `test_e2e_auth.py` | `_TABLES` truncate, `client` fixture (AsyncClient `https://test`, override fakes), helpers onboard/verify/login |

### Frontend — molde de la rebanada de identidad (esta sesión)
| Prio | File | Why |
|---|---|---|
| P0 | `src/api/http-client.ts` + `api-error.ts` + `token-store.ts` | `HttpClient` port + `FetchHttpClient` (Bearer, refresh-on-401, `{code,message}`→ApiError) — **reusar tal cual** |
| P0 | `src/api/auth-api.ts` | Molde de cliente inyectable (clase que toma `HttpClient`) → `OrdersApi`/`ProductsApi`/`TablesApi` |
| P0 | `src/services/services-context.ts` + `services-provider.tsx` | DI: agregar los nuevos clientes a `Services` |
| P0 | `src/hooks/use-*.ts` | `useQuery`/`useMutation` sobre `useServices()` → molde para use-orders/use-products/use-kds |
| P0 | `src/auth/require-role.tsx` + `src/app/router.tsx` | Guard por rol + rutas protegidas |
| P0 | `src/features/identity/*-page.tsx` + `components/ui/*` | RHF+zod, shadcn (`Card/Field/Input/Select/Button/Spinner/sonner`), tokens de tema, kebab-case |

---

## External Documentation

| Topic | Source | Key Takeaway |
|---|---|---|
| TanStack Query polling | tanstack.com/query | `useQuery({ queryKey, queryFn, refetchInterval: 5000 })` para el KDS; `refetchOnWindowFocus` ya viene útil |
| SQLAlchemy aggregate (parent+children) | docs.sqlalchemy.org | Cargar `Order` + `order_items` por separado y mapear a la entidad; en `save` sincronizar la colección (borrar faltantes + merge presentes) dentro de una transacción |

> El resto son patrones internos ya establecidos. **No external research adicional necesaria.**

---

## Patterns to Mirror

> Snippets reales en los archivos de *Mandatory Reading*. Acá, las **formas nuevas** que se derivan.

### MONEY_VALUE_OBJECT (nuevo, transversal)
```python
# app/domain/shared/money.py  — MIRROR: value_objects.py Email (frozen + __post_init__)
from dataclasses import dataclass
_ISO_4217 = {"ARS", "USD", "EUR", "BRL", "UYU", "CLP", "PYG"}

@dataclass(frozen=True)
class Money:
    """Monto en unidad mínima (centavos) + moneda ISO-4217. NUNCA float."""
    amount: int          # minor units (e.g. centavos)
    currency: str

    def __post_init__(self) -> None:
        cur = self.currency.upper()
        if cur not in _ISO_4217:
            raise UnsupportedCurrency()
        if self.amount < 0:
            raise InvalidMoneyAmount()
        object.__setattr__(self, "currency", cur)

    def times(self, qty: int) -> "Money":
        return Money(self.amount * qty, self.currency)

    def plus(self, other: "Money") -> "Money":
        if other.currency != self.currency:
            raise CurrencyMismatch()
        return Money(self.amount + other.currency_safe_amount(self), self.currency)
    # (impl simple: sumar amounts validando misma moneda)
```
**GOTCHA:** en DB el monto va como **`BigInteger` (entero)** + columna `currency String(3)` — **NO `DECIMAL`/float** (la sugerencia DECIMAL del explorador queda anulada por la decisión multi-moneda del PRD).

### ORDER_STATUS_ENUM
```python
# app/domain/order/value_objects.py — MIRROR: Role (StrEnum)
from enum import StrEnum
class OrderStatus(StrEnum):
    OPEN = "OPEN"; SENT = "SENT"; PREPARING = "PREPARING"
    READY = "READY"; SERVED = "SERVED"; CANCELLED = "CANCELLED"
```

### ORDER_AGGREGATE (entidad con máquina de estados)
```python
# app/domain/order/entities.py — MIRROR: User (dataclass no-frozen + métodos de negocio)
@dataclass
class OrderItem:
    id: str; product_id: str; name: str; unit_price: Money; quantity: int; note: str | None = None
    def line_total(self) -> Money: return self.unit_price.times(self.quantity)

@dataclass
class Order:
    id: str; tenant_id: str; table_id: str; waiter_id: str
    currency: str; status: OrderStatus
    items: list[OrderItem] = field(default_factory=list)
    created_at: datetime | None = None

    def add_item(self, item: OrderItem) -> None:
        if self.status is not OrderStatus.OPEN: raise InvalidOrderTransition()
        if item.unit_price.currency != self.currency: raise CurrencyMismatch()
        self.items.append(item)
    def send_to_kitchen(self) -> None:
        if self.status is not OrderStatus.OPEN: raise InvalidOrderTransition()
        if not self.items: raise EmptyOrder()
        self.status = OrderStatus.SENT
    def start_preparing(self) -> None: self._advance(OrderStatus.SENT, OrderStatus.PREPARING)
    def mark_ready(self) -> None: self._advance(OrderStatus.PREPARING, OrderStatus.READY)
    def mark_served(self) -> None: self._advance(OrderStatus.READY, OrderStatus.SERVED)
    def cancel(self) -> None:
        if self.status in (OrderStatus.SERVED, OrderStatus.CANCELLED): raise InvalidOrderTransition()
        self.status = OrderStatus.CANCELLED
    def total(self) -> Money:
        total = Money(0, self.currency)
        for it in self.items: total = total.plus(it.line_total())
        return total
    def _advance(self, frm: OrderStatus, to: OrderStatus) -> None:
        if self.status is not frm: raise InvalidOrderTransition()
        self.status = to
```

### AGGREGATE_REPOSITORY (parent + children)
```python
# app/infrastructure/persistence/order_repo.py — MIRROR: user_repo.py + carga de colección
async def get_by_id(self, tenant_id, order_id) -> Order | None:
    async with self._session_factory() as session:
        o = (await session.execute(select(OrderORM).where(
            OrderORM.id==order_id, OrderORM.tenant_id==tenant_id))).scalar_one_or_none()
        if o is None: return None
        items = (await session.execute(select(OrderItemORM).where(
            OrderItemORM.order_id==order_id, OrderItemORM.tenant_id==tenant_id)
            .order_by(OrderItemORM.position))).scalars().all()
        return order_to_domain(o, items)
async def save(self, order) -> None:
    async with self._session_factory() as session:
        await session.merge(order_to_orm(order))
        # sync items: borrar los que ya no están, merge de los presentes
        await session.execute(delete(OrderItemORM).where(
            OrderItemORM.order_id==order.id, OrderItemORM.tenant_id==order.tenant_id))
        for pos, it in enumerate(order.items):
            session.add(order_item_to_orm(it, order, pos))
```
**GOTCHA:** `order_items.tenant_id` se incluye (RLS por tabla). El borrado+reinserción de ítems es simple y correcto para la escala MVP (los IDs de ítem pueden rotar — aceptable en esta fase).

### FRONTEND_DATA_CLIENT
```ts
// src/api/orders-api.ts — MIRROR: src/api/auth-api.ts
export class OrdersApi {
  private http: HttpClient
  constructor(http: HttpClient) { this.http = http }
  list(status?: string) { return this.http.request<OrderDTO[]>("GET", `/orders${status?`?status=${status}`:""}`, { auth: true }) }
  create(tableId: string) { return this.http.request<OrderDTO>("POST", "/orders", { body: { table_id: tableId }, auth: true }) }
  addItem(id: string, productId: string, quantity: number, note?: string) { return this.http.request<OrderDTO>("POST", `/orders/${id}/items`, { body: { product_id: productId, quantity, note }, auth: true }) }
  send(id: string) { return this.http.request<OrderDTO>("POST", `/orders/${id}/send`, { auth: true }) }
  kds() { return this.http.request<OrderDTO[]>("GET", "/kds/orders", { auth: true }) }
  advance(id: string, action: "preparing"|"ready"|"served"|"cancel") { return this.http.request<OrderDTO>("POST", `/orders/${id}/${action}`, { auth: true }) }
}
```

### KDS_POLLING_HOOK
```ts
// src/hooks/use-kds-orders.ts — MIRROR: src/hooks/use-me pattern + refetchInterval
export function useKdsOrders() {
  const { ordersApi } = useServices()
  return useQuery({ queryKey: ["kds-orders"], queryFn: () => ordersApi.kds(), refetchInterval: 5000 })
}
```

---

## Files to Change

### Backend (mayoría CREATE; imitando Fase 1)
| File | Action |
|---|---|
| `app/domain/shared/money.py` (+ `exceptions.py`) | CREATE — `Money` VO + `UnsupportedCurrency/InvalidMoneyAmount/CurrencyMismatch` |
| `app/domain/table/{entities,exceptions,repository}.py` | CREATE — `Table` + `TableNotFound` + `TableRepository` |
| `app/domain/product/{entities,exceptions,repository}.py` | CREATE — `Product` + `ProductNotFound/InactiveProduct` + `ProductRepository` |
| `app/domain/order/{entities,value_objects,exceptions,repository}.py` | CREATE — `Order/OrderItem`, `OrderStatus`, `OrderNotFound/InvalidOrderTransition/EmptyOrder`, `OrderRepository` |
| `app/domain/tenant/entities.py` | UPDATE — agregar `country: str="AR"`, `currency: str="ARS"` |
| `app/application/{table,product,order}/dtos.py` + use cases | CREATE — `CreateTable/CreateProduct/ListProducts`; `CreateOrder/AddOrderItem/SendOrder/AdvanceOrder/ListOrders/GetKdsOrders` |
| `app/infrastructure/persistence/models.py` | UPDATE — `TableORM/ProductORM/OrderORM/OrderItemORM` + cols `country/currency` en `tenants` |
| `app/infrastructure/persistence/mappers.py` | UPDATE — mappers nuevos + tenant con currency |
| `app/infrastructure/persistence/{table_repo,product_repo,order_repo}.py` | CREATE |
| `app/presentation/api/v1/{tables,products,orders,kds}.py` | CREATE — routers |
| `app/presentation/schemas/{tables,products,orders}.py` | CREATE — Pydantic (montos como int minor units + currency) |
| `app/presentation/errors.py` | UPDATE — registrar nuevas excepciones en `_STATUS_BY_TYPE` |
| `app/main.py` | UPDATE — `include_router` de los nuevos routers |
| `app/container.py` | UPDATE — repos + use cases (Factory) |
| `alembic/versions/0002_orders_kds.py` | CREATE — tablas `tables/products/orders/order_items` (ENABLE+FORCE RLS + policy), ALTER `tenants` add country/currency, agregar las tablas a los GRANTs |
| `tests/fakes/__init__.py` | UPDATE — fakes + Harness builders/seed |
| `tests/unit/test_{money,order,product}*.py` | CREATE |
| `tests/integration/test_e2e_orders.py` + `conftest.py` | CREATE/UPDATE (`_TABLES`) |

### Frontend (CREATE salvo router/services)
| File | Action |
|---|---|
| `src/api/types-operations.ts` | CREATE — `ProductDTO/TableDTO/OrderDTO/OrderItemDTO`, `OrderStatus` |
| `src/api/{orders-api,products-api,tables-api}.ts` | CREATE — clientes inyectables |
| `src/services/services-context.ts` + `services-provider.tsx` | UPDATE — agregar `ordersApi/productsApi/tablesApi` |
| `src/lib/money.ts` | CREATE — formateo `formatMoney(amount, currency)` (Intl.NumberFormat) |
| `src/hooks/use-products.ts` `use-tables.ts` `use-orders.ts` `use-kds-orders.ts` | CREATE |
| `src/features/floor/floor-page.tsx` | CREATE — grilla de mesas (mozo) |
| `src/features/orders/order-page.tsx` | CREATE — armar comanda (elegir productos, total, enviar) |
| `src/features/kds/kds-page.tsx` | CREATE — board cocina (polling) |
| `src/features/products/products-page.tsx` | CREATE — alta/lista (admin) |
| `src/app/router.tsx` | UPDATE — rutas `/app/floor`, `/app/orders/:tableId`, `/app/kds`, `/app/products` con `RequireRole` |
| `src/features/identity/home-page.tsx` | UPDATE — links según rol (floor/kds/products) |
| `src/test/*` | CREATE — tests de money format, order-api, kds hook |

## NOT Building
- **Pagos / cobro** (Fase 3) — la comanda se cierra como `SERVED`, sin pago todavía.
- **Facturación AFIP** (Fase 4).
- **Stock/descuento por receta** (Fase 6) — `Product` ahora es solo catálogo (nombre+precio+categoría+activo).
- **Realtime con SSE/WebSockets** — MVP con **polling** (TanStack Query `refetchInterval`).
- **Edición/replanteo avanzado de comanda** (split, merge de mesas, transferencias) — solo agregar ítems mientras está OPEN.
- **Multi-idioma** — UX en español.
- **Onboarding de moneda en la UI** — el tenant default `AR/ARS` (columnas con server_default); cambiar moneda por UI es posterior.

---

## Step-by-Step Tasks

> Orden: **backend de catálogo → comandas/KDS → frontend**. Validar con `tsc/ruff/mypy/pytest` después de cada bloque. Se puede commitear en el límite backend↔frontend.

### Task 1 — `Money` VO + excepciones compartidas
- **ACTION**: crear `app/domain/shared/money.py` y `app/domain/shared/exceptions.py`.
- **IMPLEMENT**: `Money(amount:int, currency:str)` frozen con `__post_init__` (valida ISO-4217 ∈ set soportado, amount≥0), `times(qty)`, `plus(other)` (misma moneda), `zero(currency)`, `__str__`. Excepciones `UnsupportedCurrency/InvalidMoneyAmount/CurrencyMismatch` (DomainError, code EN + message ES).
- **MIRROR**: `MONEY_VALUE_OBJECT`; `Email`/`DomainError`.
- **GOTCHA**: enteros, nunca float; `object.__setattr__` para normalizar currency en frozen.
- **VALIDATE**: `pytest tests/unit/test_money.py` (suma, distinta moneda lanza, negativo lanza, moneda inválida lanza).

### Task 2 — Tenant: agregar país/moneda
- **ACTION**: extender el tenant con `country`/`currency`.
- **IMPLEMENT**: `Tenant` entity → `country: str="AR"`, `currency: str="ARS"`. `TenantORM` → columnas `country String(2) server_default 'AR'`, `currency String(3) server_default 'ARS'`. Actualizar `tenant_to_domain/tenant_to_orm`.
- **MIRROR**: `models.py` TenantORM, `mappers.py`.
- **GOTCHA**: defaults en la entidad para no romper `Tenant(id,slug,name)` existente; server_default en la columna para filas viejas.
- **VALIDATE**: `mypy app`; el onboarding e2e existente sigue verde.

### Task 3 — Dominio `Table` y `Product`
- **ACTION**: crear los paquetes de dominio `table/` y `product/`.
- **IMPLEMENT**: `Table(id,tenant_id,number:int,name:str|None,active:bool=True,created_at)`. `Product(id,tenant_id,name,price:Money,category:str|None,active:bool=True,created_at)` con método `deactivate()`. Excepciones `TableNotFound`, `ProductNotFound/InactiveProduct`. Ports `TableRepository`/`ProductRepository` (ABC async, `tenant_id` en cada método: get_by_id, list/list_active, add, save).
- **MIRROR**: `User` entity, `repository.py` ABC, `exceptions.py`.
- **VALIDATE**: `mypy app`.

### Task 4 — Dominio `Order` (agregado + máquina de estados)
- **ACTION**: crear `order/` (entities, value_objects, exceptions, repository).
- **IMPLEMENT**: `OrderStatus` (StrEnum), `OrderItem`, `Order` aggregate con métodos `add_item/send_to_kitchen/start_preparing/mark_ready/mark_served/cancel/total/_advance` (ver `ORDER_AGGREGATE`). `OrderNotFound/InvalidOrderTransition/EmptyOrder`. `OrderRepository` (get_by_id, list_by_status, list_kds, add, save).
- **MIRROR**: `User` (métodos de negocio que levantan DomainError), `ORDER_STATUS_ENUM`.
- **GOTCHA**: invariantes en la entidad (no agregar ítems si no está OPEN; enviar requiere ítems; transiciones válidas). Moneda del ítem == moneda de la order.
- **VALIDATE**: `pytest tests/unit/test_order.py` (lifecycle válido + transiciones inválidas lanzan + total suma).

### Task 5 — Registrar excepciones en el handler
- **ACTION**: `app/presentation/errors.py` → agregar a `_STATUS_BY_TYPE`: `TableNotFound`(404), `ProductNotFound`(404), `InactiveProduct`(409), `OrderNotFound`(404), `InvalidOrderTransition`(409), `EmptyOrder`(422), `UnsupportedCurrency`(422), `CurrencyMismatch`(422), `InvalidMoneyAmount`(422).
- **MIRROR**: `errors.py` lista existente.
- **VALIDATE**: `mypy app`.

### Task 6 — ORM models + mappers
- **ACTION**: agregar `TableORM/ProductORM/OrderORM/OrderItemORM` y sus mappers.
- **IMPLEMENT**: cada tabla tenant-scoped: `id Uuid`, `tenant_id Uuid FK→tenants ondelete CASCADE index`, `created_at server_default func.now()`. `ProductORM`: `price_amount BigInteger`, `price_currency String(3)`, `name String`, `category String|None`, `active Boolean`. `OrderORM`: `table_id Uuid index`, `waiter_id Uuid`, `status String(20)`, `currency String(3)`. `OrderItemORM`: `order_id Uuid index`, `tenant_id`, `product_id Uuid`, `name String`, `unit_price_amount BigInteger`, `quantity Integer`, `note String|None`, `position Integer`. Mappers `*_to_domain`/`*_to_orm` (omitir created_at en `_to_orm`); `order_to_domain(orm, items)` arma `Money(price_amount, currency)`.
- **MIRROR**: `models.py` UserORM, `mappers.py`.
- **GOTCHA**: **`BigInteger` para montos** (no DECIMAL). `order_items` lleva `tenant_id` (RLS).
- **VALIDATE**: `mypy app`.

### Task 7 — Repositorios SQLAlchemy
- **ACTION**: `table_repo.py`, `product_repo.py`, `order_repo.py`.
- **IMPLEMENT**: filtro `tenant_id` explícito en todo WHERE; `add`=session.add, `save`=session.merge; `OrderRepository.get_by_id` carga ítems aparte y mapea (ver `AGGREGATE_REPOSITORY`); `save` sincroniza ítems (delete + re-add en la misma transacción); `list_kds` = status ∈ {SENT, PREPARING} ordenado por created_at asc.
- **MIRROR**: `user_repo.py`, `AGGREGATE_REPOSITORY`.
- **VALIDATE**: `mypy app`; cubierto por integración (Task 12).

### Task 8 — Migración Alembic 0002 (+ RLS)
- **ACTION**: `alembic/versions/0002_orders_kds.py` (down_revision `0001_initial`).
- **IMPLEMENT**: `ALTER TABLE tenants ADD COLUMN country/currency` (server_default 'AR'/'ARS'); `create_table` para tables/products/orders/order_items; por cada nueva tabla tenant-scoped: `ENABLE`+`FORCE ROW LEVEL SECURITY` + `CREATE POLICY tenant_isolation ... current_setting('app.tenant_id', true)::uuid`. Asegurar GRANTs al rol `bravo_app` (las nuevas tablas heredan por `ALTER DEFAULT PRIVILEGES`, verificar). `downgrade` simétrico.
- **MIRROR**: `0001_initial.py` (bloque RLS textual).
- **GOTCHA**: la policy va en las 4 tablas nuevas (incl. `order_items`). `tenants` NO es tenant-scoped (no policy).
- **VALIDATE**: `poetry run alembic upgrade head` sobre la DB de test; luego `alembic downgrade -1 && upgrade head`.

### Task 9 — Casos de uso (application)
- **ACTION**: use cases + DTOs por módulo.
- **IMPLEMENT**:
  - Product: `CreateProduct(tenant_id, name, price:Money, category)`, `ListProducts(tenant_id, only_active)`.
  - Table: `CreateTable(tenant_id, number, name)`, `ListTables(tenant_id)`.
  - Order: `CreateOrder(*, tenant_id, waiter_id, table_id)` (toma currency del tenant), `AddOrderItem(*, tenant_id, order_id, product_id, quantity, note)` (lee Product, snapshot name+price, valida activo y OPEN), `SendOrder`, `AdvanceOrder(*, tenant_id, order_id, action)` (preparing/ready/served/cancel → método del agregado), `ListOrders(tenant_id, status?)`, `GetKdsOrders(tenant_id)`.
- **MIRROR**: `onboard_tenant.py`/`invite_user.py` (ctor inyecta ports, `async execute(*,...)`, `tenant_context.set(tenant_id)`, `str(uuid4())`, `utcnow()`, levanta DomainError).
- **GOTCHA**: `AddOrderItem` toma el precio del `Product` (snapshot), no del cliente. `CreateOrder` setea `order.currency = tenant.currency`.
- **VALIDATE**: `pytest tests/unit/test_order_usecases.py`.

### Task 10 — Schemas + routers + wiring
- **ACTION**: Pydantic schemas, routers, `container.py`, `main.py`.
- **IMPLEMENT**: schemas request/response (montos como `int` minor units + `currency`; `OrderResponse` con items + total + status). Routers con `@inject` + `require_roles`:
  - `products`: `POST` (OWNER/MANAGER), `GET` (cualquiera autenticado).
  - `tables`: `POST` (OWNER/MANAGER), `GET` (cualquiera).
  - `orders`: `POST`/`/items`/`/send`/`/served` (WAITER/MANAGER/OWNER), `/preparing`,`/ready` (KITCHEN/MANAGER/OWNER), `/cancel` (MANAGER/OWNER), `GET`/`GET {id}` (cualquiera).
  - `kds`: `GET /kds/orders` (KITCHEN/MANAGER/OWNER).
  Container: `providers.Factory` para repos + use cases. `main.py`: `include_router(... prefix="/api/v1")`.
- **MIRROR**: `users.py`/`tenants.py` routers, `schemas/users.py`, `container.py`, `main.py`.
- **GOTCHA**: usar `AccessClaims` de `require_roles(...)` para `tenant_id`/`user_id`(waiter)/`role`.
- **VALIDATE**: `ruff check . && mypy app`; app levanta.

### Task 11 — Fakes + unit tests
- **ACTION**: fakes in-memory + Harness builders.
- **IMPLEMENT**: `FakeTableRepository/FakeProductRepository/FakeOrderRepository` (filtran tenant_id); agregar a `Harness` + builders de use cases + `seed_product/seed_table`. Tests unitarios de los use cases (crear orden, agregar ítem snapshotea precio, enviar vacía lanza `EmptyOrder`, transición inválida lanza, KDS lista solo SENT/PREPARING).
- **MIRROR**: `tests/fakes/__init__.py`, `test_auth_core.py`.
- **VALIDATE**: `pytest tests/unit -q`.

### Task 12 — Integration e2e (DB real + RLS)
- **ACTION**: `tests/integration/test_e2e_orders.py`; actualizar `_TABLES` con `order_items, orders, products, tables`.
- **IMPLEMENT**: flujo onboard→verify→login (OWNER) → crear product → crear table → crear order → add item → send → (login KITCHEN vía invitación o seed) `GET /kds/orders` lo ve → preparing → ready → served. Verificar aislamiento RLS (un tenant no ve órdenes de otro).
- **MIRROR**: `test_e2e_auth.py` helpers + `conftest.py`.
- **VALIDATE**: `pytest tests/integration -q`.

### Task 13 — Frontend: clientes + DI + tipos + money
- **ACTION**: capa de datos del front.
- **IMPLEMENT**: `types-operations.ts` (DTOs + `OrderStatus`), `orders-api.ts/products-api.ts/tables-api.ts` (MIRROR `auth-api.ts`), agregar a `Services` + `ServicesProvider`. `lib/money.ts`: `formatMoney(amount:number, currency:string)` con `Intl.NumberFormat('es-AR',{style:'currency',currency})` (amount/100).
- **MIRROR**: `src/api/auth-api.ts`, `services-context.ts`.
- **VALIDATE**: `npm run typecheck`.

### Task 14 — Frontend: hooks
- **ACTION**: `use-products/use-tables/use-orders/use-kds-orders`.
- **IMPLEMENT**: queries + mutations sobre `useServices()`; `use-kds-orders` con `refetchInterval:5000`. Invalidar queries tras mutaciones (`queryClient.invalidateQueries`).
- **MIRROR**: `src/hooks/use-*.ts`, `KDS_POLLING_HOOK`.
- **VALIDATE**: `npm run typecheck`.

### Task 15 — Frontend: pantallas + router + guards
- **ACTION**: floor, order, kds, products pages + rutas.
- **IMPLEMENT**:
  - `floor-page` (`/app/floor`): grilla de mesas → click crea/abre orden → navega a `/app/orders/:tableId`.
  - `order-page` (`/app/orders/:tableId`): lista de productos (buscar), agregar ítem (cantidad+nota), total en vivo (`formatMoney`), botón Enviar a cocina. 
  - `kds-page` (`/app/kds`): board de cards por orden (mesa + ítems), botones Preparar/Listo; polling 5s; estados con tokens de tema.
  - `products-page` (`/app/products`): lista + form alta (nombre, precio, categoría) con RHF+zod.
  - `router.tsx`: rutas bajo `RequireAuth` + `RequireRole` (floor/orders: WAITER/MANAGER/OWNER; kds: KITCHEN/MANAGER/OWNER; products: OWNER/MANAGER). `home-page`: links por rol.
- **MIRROR**: `features/identity/*-page.tsx`, `require-role.tsx`, `router.tsx`, shadcn (`Card/Field/Input/Select/Button/Spinner/sonner`).
- **GOTCHA**: precios en el form se ingresan en unidades (ej. 1500.00) → convertir a minor units (×100, entero) antes de enviar. Mensajes/labels en español.
- **VALIDATE**: `npm run build`; `npm run dev` y recorrer el flujo.

### Task 16 — Frontend tests + cierre
- **ACTION**: tests de alto valor + validación final.
- **IMPLEMENT**: test de `formatMoney`, de `orders-api` (body correcto), de `kds` hook (usa refetchInterval / render con fake). `npm run lint && test && build`.
- **MIRROR**: `src/test/test-utils.tsx`, tests de identidad.
- **VALIDATE**: `npm run lint && npm run test && npm run build`.

---

## Testing Strategy

### Unit
| Test | Input | Expected | Edge? |
|---|---|---|---|
| Money.plus distinta moneda | ARS + USD | lanza `CurrencyMismatch` | sí |
| Money negativo / moneda inválida | -1 / "XXX" | lanza | sí |
| Order.send_to_kitchen vacía | sin ítems | lanza `EmptyOrder` | sí |
| Order transición inválida | OPEN→READY | lanza `InvalidOrderTransition` | sí |
| AddOrderItem snapshot | product price 1500 | item.unit_price = 1500, no relee al cambiar product | sí |
| GetKdsOrders | órdenes en varios estados | solo SENT/PREPARING | sí |
| Order.total | 2×1500 + 1×800 | 3800 ARS | — |

### Edge Cases Checklist
- [ ] Agregar ítem a orden ya enviada → error
- [ ] Producto inactivo → no se puede agregar
- [ ] Aislamiento RLS: tenant A no ve órdenes/products de tenant B
- [ ] Moneda del ítem ≠ moneda de la orden → error
- [ ] KDS de un tenant solo muestra sus órdenes
- [ ] Rol incorrecto en cada endpoint → 403
- [ ] Precio en el front (1500.50) → 150050 minor units

---

## Validation Commands

### Backend
```bash
cd backend
poetry run ruff check . && poetry run mypy app
poetry run alembic upgrade head           # aplica 0002 (+ downgrade -1 && upgrade head para verificar reversibilidad)
poetry run pytest tests/unit tests/integration -q
```
EXPECT: ruff/mypy limpios; migración up/down ok; tests verdes.

### Frontend
```bash
npm run typecheck && npm run lint && npm run test && npm run build
```
EXPECT: cero errores; tests verdes.

### Manual / E2E local
```bash
# backend con logs (para ver links de invitación al sembrar un KITCHEN)
cd backend && PYTHONUNBUFFERED=1 poetry run uvicorn app.main:app --reload --port 8000
npm run dev   # :5173 (proxy /api)
```
- [ ] OWNER crea 2-3 productos en `/app/products`.
- [ ] WAITER en `/app/floor` → mesa → arma comanda → Enviar a cocina.
- [ ] KITCHEN en `/app/kds` ve la comanda (≤5s) → Preparar → Listo.
- [ ] WAITER marca Servido. Otro tenant no ve nada de este.

---

## Acceptance Criteria
- [ ] Mozo crea comanda con ítems (precio snapshot) y la envía; cocina la ve en KDS en ≤5s y avanza estados.
- [ ] `Money` (entero + ISO-4217) en dominio y DB (BigInteger); sin float; moneda por tenant (default ARS).
- [ ] Todas las tablas nuevas tenant-scoped con RLS policy; aislamiento verificado.
- [ ] RBAC por endpoint correcto (WAITER/KITCHEN/MANAGER/OWNER).
- [ ] backend ruff+mypy+pytest verdes; migración up/down; front tsc+lint+test+build verdes.

## Completion Checklist
- [ ] Código imita Fase 1 (entidad/VO/exception/port/usecase/router/repo/migration/test)
- [ ] Errores `{code EN, message ES}` registrados en el handler
- [ ] Filtro `tenant_id` explícito en cada repo + RLS en cada tabla
- [ ] Sin float para plata; montos enteros en unidad mínima
- [ ] Frontend reusa http-client/DI/guards/TanStack/shadcn; UX en español
- [ ] Autocontenido — sin búsquedas extra durante implementación

## Risks
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Persistencia de agregado (Order+items) | M | M | Patrón delete+re-add en transacción; cubierto por integración |
| RLS en `order_items` mal configurada | M | A | Migración con policy en las 4 tablas; test de aislamiento explícito |
| Alcance XL en una pasada | A | M | Partir en commits backend↔frontend; tasks ordenadas; catálogo antes que comandas |
| Float/redondeo en plata | M | A | `Money` entero + BigInteger desde Task 1; conversión ×100 en el borde del front |
| Polling del KDS cuesta requests | B | B | `refetchInterval` 5s alcanza para un local; SSE/WS es follow-up |

## Notes
- Esta fase **introduce el `Money` VO y la moneda por tenant** (decisión multi-moneda del PRD) — infra que reusa todo el motor.
- `Product` es solo catálogo (nombre+precio+categoría+activo); stock/receta llega en Fase 6.
- La comanda termina en `SERVED` sin pago (Fase 3) ni factura (Fase 4).
- Decisión deliberada: **polling** para el KDS (no SSE/WS) en el MVP.
