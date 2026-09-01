# Plan — Carta QR, Fase 1 (solo ver) + sesión de mesa + llamar al mozo / pedir la cuenta

> **Estado:** Plan (NO codeado). Creado 2026-08-27. Deriva de `prds/carta-qr-autopedido.prd.md`.
> **Objetivo de la fase:** el comensal escanea el QR de su mesa y ve la **carta digital** (bilingüe), y puede **llamar al mozo** o **pedir la cuenta**. **Sin** pedir ni pagar todavía (eso es Fase 2/3). Deja montado el **plumbing de sesión de mesa** que reusan las fases siguientes.
> **Por qué primero:** bajo riesgo, alto valor (reemplaza el PDF), y el 80% del motor ya existe.

## Defaults asumidos (de las decisiones del PRD, para no trabar la fase)
- **QR estático por mesa** (impreso) + **token firmado**; el "PIN de mesa" se difiere a cuando haya pedido/pago (F2/F3). En F1 el token alcanza (solo lee la carta pública, que no es sensible).
- **Front = ruta nueva dentro de la app** `frontend/` (`/carta/:token`), pública (sin auth), mobile-first, **reusa tema + i18n**.
- Carta = catálogo actual (`Product`: name/price/category/active). Fotos/descripciones/modificadores llegan en F2.

---

## Alcance

**Incluye:** sesión de mesa pública, endpoint público de carta por token, página pública de carta (bilingüe), acciones "llamar al mozo" / "pedir la cuenta" que notifican al salón, y una pantalla para que el dueño obtenga/imprima los QR por mesa.

**NO incluye (F2/F3):** carrito, crear comanda, pago, modificadores, disponibilidad "86'd", identificación del comensal, PIN rotativo.

---

## Backend (`backend/`)

Arquitectura de siempre: dominio puro → casos de uso sobre ports → adapters en infra → DI en `container.py` → RLS por `tenant_id`. Molde de referencia: **timeclock presence** (QR + token firmado) y **`public.py`** (router sin auth).

1. **Dominio `table_session`** (nuevo, `app/domain/table_session/`):
   - Entidad `TableSession` (`tenant_id`, `table_id`, `token`, `opened_at`, `expires_at?`, `status`).
   - Port `TableSessionTokenService` (firmar/verificar token) — reusar el mismo esquema de token firmado del presence challenge (`app/domain/identity` / presence) para no reinventar.
   - Excepciones: `InvalidTableSession`, `ExpiredTableSession`.
2. **Persistencia** (`app/infrastructure/persistence/`): tabla `table_sessions` (RLS), ORM + mapper + `SqlAlchemyTableSessionRepository`. Migración **0028** (siguiente a la 0027).
   - *Alternativa liviana para F1:* si el token es autocontenido (firma `tenant_id`+`table_id`), la sesión puede ser **stateless** (sin tabla) hasta F2. Decidir en implementación; el plan asume stateless en F1 para minimizar superficie, y la tabla entra en F2 cuando haya carrito/estado.
3. **Casos de uso** (`app/application/table_session/` + `app/application/menu/`):
   - `IssueTableQr(table_id) -> token/url` (protegido, OWNER/MANAGER): genera el token/URL del QR de una mesa.
   - `GetPublicMenu(token) -> MenuDTO`: valida el token → resuelve `tenant_id` → devuelve la carta pública (categorías + productos activos, precio). **Reusa el read-model de productos** (el mismo que alimenta `/analytics/products` / catálogo), filtrando `active` y exponiendo solo lo público (sin costo/food-cost).
   - `RequestWaiter(token)` / `RequestBill(token)`: validan el token y emiten un **evento de realtime** al salón (reusa la infra SSE de `realtime.py`/KDS) — el floor/caja recibe "Mesa N te llama" / "Mesa N pide la cuenta".
4. **Router público** (`app/presentation/api/v1/public.py`, extender): 
   - `GET /public/menu?token=…` → carta.
   - `POST /public/table/call-waiter` / `POST /public/table/request-bill` (body con token) → notifican.
   - Sin auth (molde `public.py`/`leads.py`); rate-limit básico; el token porta el tenant.
   - Endpoint protegido `POST /tables/{id}/qr` (o `/floor/...`) para `IssueTableQr`.
5. **Realtime**: publicar los eventos "call_waiter"/"request_bill" por el canal del tenant (reusar el bus/SSE existente de KDS/floor). El floor/caja del front se suscribe.
6. **Tests** (80%+ dominio/uso): token válido/expirado/de otro tenant (aislamiento), carta solo-activos-y-sin-costo, request-waiter emite evento, RBAC del `IssueTableQr`.

## Frontend (`frontend/`)

1. **Ruta pública** `/carta/:token` (o `/carta?token=…`) en `app/router.tsx`, **fuera** del `RequireAuth` (como `/login`), mobile-first.
2. **Página de carta pública** (`features/public-menu/` nuevo): consume `GET /public/menu?token=…` vía un cliente de API inyectable (no `fetch` suelto). Render: header con branding del local, categorías, ítems (nombre, precio, y foto/descr. cuando existan en F2). **Bilingüe** (reusa `useTranslation` + un namespace `publicMenu`; el idioma por navegador, más adelante por `tenant.locale`).
3. **Acciones** "Llamar al mozo" / "Pedir la cuenta": botones que llaman a los endpoints públicos; feedback (toast) "El mozo ya viene".
4. **Gestión de QR (lado dueño):** en `floor`/`settings`, un botón por mesa "Ver/Imprimir QR" que pega a `IssueTableQr` y muestra el QR (generar el QR en el cliente con una lib liviana o `<img>` a un data-URL). Imprimible.
5. **Estados:** token inválido/expirado → pantalla amable ("Pedile el QR al mozo").

## Validación (gates del proyecto)
- Backend: `poetry run pytest` (80%+ en dominio/uso nuevos) + `ruff`.
- Frontend: `npm run build` (tsc) + `npm run lint` + tests. **Gate real = `npm run build`** (no `tsc --noEmit`).
- Visual: carta pública en mobile, ES y EN; "llamar al mozo" llega al floor en vivo.
- Multi-tenant: token de un tenant NO ve la carta de otro (aislamiento) — test explícito.

## Riesgos / notas
- **Seguridad del token:** en F1 solo lee carta pública (bajo riesgo). Endurecer (PIN, expiración corta, rotación) llega con pedido/pago en F2/F3.
- **Stateless vs tabla:** F1 puede ser stateless (token autocontenido). La tabla `table_sessions` se justifica en F2 (carrito/estado por mesa). No adelantar complejidad.
- **Realtime:** reusar el bus existente; no crear uno nuevo.
- **i18n del contenido:** los nombres de producto los carga el dueño (español); la **UI** de la carta es bilingüe, el **contenido** queda en el idioma que cargó el local (igual que hoy). Traducción de contenido = fuera de scope.

## Troceo sugerido (tandas)
- **A — Sesión + carta (backend): ✅ HECHA.** Contexto nuevo `public_menu` (NO se tocó el `table_session` del floor, que es la visita/turno de mesa — colisión de nombre evitada). Token firmado **stateless** `HmacTableQrToken` (molde: presence device token) → sin migración. `IssueTableQr` (`GET /tables/{id}/qr`, RBAC OWNER/MANAGER, idempotente) + `GetPublicMenu` (`GET /public/menu?token=…`, sin auth, solo activos y sin costos, agrupado por categoría). Error `invalid_table_qr_token` → 401. Config `table_qr_secret` (cae a `jwt_secret`). Gates: ruff + **615 tests** (14 nuevos: token round-trip/tamper/kind, `group_menu` puro, e2e emisión→carta + aislamiento + token malo).
- **B — Carta (frontend):** ruta pública + página + cliente API + i18n + estados.
- **C — Llamar al mozo / pedir la cuenta:** endpoints + realtime + recepción en el floor.
- **D — Gestión/impresión de QR** (lado dueño).

Cada tanda cierra con sus gates. A+B ya dejan la carta QR en la calle; C+D la completan.

---

## Próximo
Aprobar este plan → `/prp-implement` por tandas (A→D). Al terminar F1, el PRD sigue con **Fase 2 (autopedido)**, que reusa la sesión de mesa de acá y agrega carrito + enriquecimiento del producto (modificadores/fotos/disponibilidad).
