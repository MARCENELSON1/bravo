# Plan — Carta QR, Fase 2 (Autopedido: carrito → comanda)

> **Estado:** Plan (NO codeado). Creado 2026-09-01. Deriva de `prds/carta-qr-autopedido.prd.md` y sucede a `carta-qr-fase-1.plan.md` (✅ completa).
> **Objetivo:** el comensal arma su pedido desde la carta QR y lo envía; cae en el pipeline real (KDS/floor) como una `Order`, con un **gate de confirmación** del mozo configurable. Requiere **enriquecer el producto** (fotos, descripción, disponibilidad, **modificadores**).
> **Por qué ahora:** F1 dejó la carta + la sesión de mesa; F2 cierra el loop operativo (el pedido entra solo). El pago (F3) va después.

## Insight de arquitectura (lo que hace esta fase barata)

Al mapear el código real, el motor ya soporta casi todo:

1. **El gate = el ciclo `PENDING` que YA existe.** `OrderItem` nace `PENDING` ("cargado, no marchado"); el mozo "marcha" (`Order.march()`: PENDING→SENT→KDS). Entonces:
   - **Gate ON (recomendado):** el autopedido crea la `Order` con ítems **PENDING y NO marcha** → el mozo lo ve en el floor y confirma = el `march()` de siempre.
   - **Gate OFF:** el submit llama `march()` en el acto (auto-marcha al KDS).
   - **No hay estado nuevo** — reusa PENDING + `march()`.
2. **La sesión de mesa ya está.** `CreateOrder` **abre o reusa** el `table_session` del floor (la visita) y cuelga la orden con `order.session_id`. El autopedido reusa esto → **NO se crea una tabla de sesión nueva** (corrige la nota vieja de F1). El token de F1 sigue siendo el scope.
3. **`OrderItem` ya snapshotea `name` + `unit_price`.** Falta solo la selección de **modificadores** (estructura nueva) y `source`.

Gaps reales a construir: **enriquecer el producto** (fotos/descr./disponibilidad/**modificadores**), el **`source`** (WAITER|CUSTOMER_QR) para métricas, el **caso de uso público de pedido**, el **carrito** en el front, y la **config del gate**.

## Defaults asumidos (de las decisiones del PRD §7)
- **Gate de cocina ON por default** (el mozo confirma), configurable por tenant. Rollout AR seguro.
- **Modificadores simples primero:** grupos con opciones + precio (min/max por grupo), **sin reglas anidadas**.
- **Comensal opcional**: nombre/teléfono opcionales (→ CRM/loyalty), o anónimo. F2 puede quedar anónimo y dejar el gancho.
- **Pago NO** (es F3): F2 crea la comanda; se paga con el mozo como hoy.
- **`waiter_id` de un pedido de cliente** (la orden lo exige): se atribuye al **mozo de la sesión** si la mesa ya está abierta; si no, a un **sentinel de sistema** que el mozo reemplaza al confirmar. (Sub-decisión menor, resuelta en implementación.)

---

## Backend (`backend/`)

Arquitectura de siempre. Reusa `public_menu` (F1), `order`, `table_session` (floor), `product`, realtime.

1. **Enriquecer el producto** (`domain/product/entities.py` hoy: `name, price, category, station, active`):
   - **+** `image_url: str | None`, `description: str | None`, `available_today: bool = True` ("86'd" = agotado hoy, distinto de `active` que es baja permanente).
   - ORM + mapper + migración. Extender `GetPublicMenu` (F1) y el catálogo del dueño para exponerlos (la carta pública muestra foto/descr.; oculta lo agotado o lo marca).
2. **Modificadores** (nuevo, lo más grande):
   - Entidades `ProductModifier` (grupo: nombre, `min_select`, `max_select`, requerido) + `ModifierOption` (nombre, `price_delta` en minor units). Tablas nuevas (RLS) + migración.
   - CRUD (OWNER/MANAGER): `/products/{id}/modifiers` GET/PUT (reusa el patrón de `SetRecipe`).
   - Exponer los grupos/opciones activos en la carta pública (F1 `GetPublicMenu` → item con sus modifier groups).
   - **Selección en el `OrderItem`:** capturar las opciones elegidas + su `price_delta` (suma al `unit_price` snapshot). Estructura: `OrderItem.selected_options` (lista de {option_id, name, price_delta} snapshoteada) — migración de `order_items`.
3. **`source` de origen:** `Order.source: OrderSource = WAITER` (+ opcional `OrderItem.source`) para métricas `CUSTOMER_QR` vs `WAITER`. Enum nuevo `OrderSource` en `domain/order/value_objects.py`. Migración (default WAITER → paridad).
4. **Caso de uso público `SubmitCustomerOrder`** (`application/public_menu/`):
   - `execute(token, lines[])`: verifica token (F1) → `tenant_id`+`table_id` → **reusa/espeja `CreateOrder`** (abre/reusa la sesión) + agrega ítems (espeja `AddOrderItemsBatch`) con `source=CUSTOMER_QR`, resolviendo precio+modificadores del catálogo (server-side, **nunca confía el precio del cliente**), validando `available_today` y grupos min/max.
   - **Gate:** si `self_order_requires_confirmation` (config) → deja los ítems **PENDING sin marchar**; si no → `march()` + eventos KDS (reusa `_kds_changed`/`_floor_changed`).
   - Emite `floor.changed` (+ `floor.call` tipo "nuevo pedido" para que el mozo lo vea, reusando la infra de F1 Tanda C).
5. **Config del tenant:** `self_order_enabled`, `self_order_requires_confirmation` (en `advisor_settings`/config del tenant, como `require_open_cash_session`). Endpoints de lectura/escritura (OWNER/MANAGER) + un guard: si `self_order_enabled` está off, `SubmitCustomerOrder` → 409.
6. **Endpoint público** `POST /public/table/order` (body: token + lines) → crea la comanda. Sin auth; el token porta el tenant+mesa; rate-limit básico.
7. **Confirmación del mozo:** el floor ya puede marchar (reusa `SendOrder`/`march`); solo hace falta que el pedido pendiente sea visible y confirmable (ver frontend).
8. **Tests (80%+):** precio/modificadores resueltos server-side (ignora precio del cliente), gate ON deja PENDING / OFF marcha, `available_today` bloquea, min/max de grupos, `source=CUSTOMER_QR`, aislamiento por token, config off → 409.

## Frontend (`frontend/`)

1. **Carta enriquecida** (extiende la página pública de F1): fotos, descripción, ítems agotados ("hoy no hay") deshabilitados. Reusa `publicMenu` i18n.
2. **Carrito + modificadores:** selección de opciones por ítem (grupos min/max), cantidades, nota; resumen del carrito; total en vivo (`formatMoney`). Cliente API inyectable (extiende `PublicMenuApi`).
3. **Enviar el pedido:** `POST /public/table/order` → pantalla de confirmación ("Tu pedido llegó a la cocina" / "El mozo lo va a confirmar" según el gate). Estado del pedido (reusa el token; opcional un `GET` de estado en F2 o diferir).
4. **Lado dueño — config:** en `settings`/`/app/mesas-qr`, toggles "Autopedido" + "Requiere confirmación del mozo"; y en el editor de producto (products-page): foto (URL/upload diferible), descripción, "disponible hoy", y **modificadores** (grupos + opciones + precio).
5. **Floor — confirmar:** el pedido `CUSTOMER_QR` pendiente aparece en el floor/comanda; el mozo lo **confirma (marcha)** con la UI existente. Un badge "pedido del cliente" (reusa `source`).

## Validación (gates del proyecto)
- Backend: `poetry run pytest` (80%+ en dominio/uso nuevos) + `ruff`.
- Frontend: `npm run build` + `npm run lint` + tests (gate real = `build`).
- Multi-tenant: token de un tenant NO pedí­ a otro; precio/modificadores server-side (un carrito manipulado NO cambia el total).
- Paridad: `source=WAITER`/`available_today=true`/sin modificadores → todo se comporta EXACTO que hoy (defaults no-breaking).

## Riesgos / notas
- **Precio de confianza:** el server SIEMPRE recalcula precio + `price_delta` desde el catálogo; el cliente solo manda ids/cantidades. (Filosofía "nunca un número inflado/manipulable".)
- **Flood de cocina:** el gate ON lo contiene; además rate-limit del endpoint.
- **Modificadores = la pieza más grande** (entidad + migración + CRUD + UI + snapshot en el ítem). Se puede trocear: carta+carrito SIN modificadores primero, modificadores después.
- **Fotos:** F2 puede aceptar `image_url` (URL pegada); el **upload** de imágenes (storage) es un incremento aparte.
- **Consumo de stock de modificadores:** fuera de scope (como el consumo de preparaciones anidadas).

## Troceo sugerido (tandas)
- **A — Enriquecimiento del producto: ✅ HECHA.** `image_url`/`description`/`available_today` en `Product` (entity+ORM+mapper) + migración **0046** (NO 0030 — la cadena real iba hasta 0045; aplicada a dev). `CreateProduct` acepta foto/descr.; `SetProductAvailability` + `PUT /products/{id}/availability` (toggle "86'd", no toca `active`). Expuesto en `GET /products` (helper `_product_response`) y en la carta pública (`GetPublicMenu` → item con foto/descr/disponibilidad). Front: DTO sincronizado + la carta muestra descripción + tag "Agotado" (fotos → Tanda C). Gates: back **626 tests**+ruff · front build+lint+**217 tests**. Todo con defaults no-breaking (paridad).
- **B — Autopedido SIN modificadores (backend): ✅ HECHA.** `OrderSource` (WAITER default | CUSTOMER_QR) en `Order` + `CreateOrder` acepta `source`. `SubmitCustomerOrder` (`application/order/self_order.py`): verifica token → guard `SelfOrderDisabled` → valida catálogo/`available_today` (`ProductUnavailable`) → **reusa `CreateOrder` (abre/reusa la sesión del floor) + `AddOrderItemsBatch`** con **precio server-side** (el cliente solo manda ids+cantidades); **el gate = el flujo PENDING** (`send=not requires_confirmation`: ON deja PENDING/OPEN, OFF marcha/SENT). `waiter_id` = el de la sesión abierta o un UUID nil sentinel. Config `SelfOrderSettings` (enabled off + requires_confirmation on por default) espejando `CashSettings` (flags en `tenants`). Endpoints: `POST /public/table/order` (sin auth) + `GET/PUT /self-order/settings` (OWNER/MANAGER). Migración **0047** (aplicada a dev). Gates: back **635 tests** + ruff. Frontend (carrito) → Tanda C.
- **C — Carrito + carta enriquecida (frontend): ✅ HECHA** (`cb635e0`). Carrito local (id→cantidad) con steppers por ítem (`+` → `[− n +]`), barra de envío con total en vivo + `POST /public/table/order`, pantalla de confirmación según el gate (mozo confirma vs directo a cocina) + "pedir algo más". Carta enriquecida: fotos (`image_url`), descripción, tag "Agotado". La carta pública ahora expone el gate (`self_order_enabled`/`requires_confirmation`) — `GetPublicMenu` lee `SelfOrderSettings` (default off = **paridad F1**: sin autopedido, la carta es idéntica a F1). i18n ES (paridad) + EN; `product_unavailable` → toast claro. Gates: back **635 tests**+ruff · front build+lint+**219 tests**. **A+B+C = autopedido MVP en la calle (sin modificadores).**
- **D — Modificadores (backend):** entidades + migración + CRUD + exponer en carta + snapshot/validación en `SubmitCustomerOrder`.
- **E — Modificadores + config (frontend):** selección de modificadores en el carrito + editor de producto (foto/descr/disponible/modificadores) + toggles de autopedido/gate + confirmación del mozo en el floor (badge `source`).

Cada tanda cierra con sus gates. A→C es el MVP del autopedido; D→E agregan modificadores y la gestión del dueño.

---

## Decisiones abiertas (confirmables antes de implementar)
Con defaults ya elegidos (arriba), pero conviene confirmar:
1. **Gate por default: ON** (el mozo confirma). ¿OK?
2. **Modificadores: simples** (grupos min/max + precio, sin reglas). ¿OK, o directo sin modificadores en F2 y dejarlos para F2.5?
3. **Comensal anónimo en F2** (identificación opcional → F3/loyalty). ¿OK?
4. **Fotos por URL** en F2 (upload de imágenes = incremento aparte). ¿OK?

## Próximo
Aprobar este plan (y las 4 decisiones) → `/prp-implement` por tandas (A→E). Al terminar F2, sigue **Fase 3 (pago desde la mesa)**: reusa `PaymentGateway.charge()` + propina + factura + dividir la cuenta.
