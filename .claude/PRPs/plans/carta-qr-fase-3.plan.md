# Plan — Carta QR, Fase 3 (Pago desde la mesa)

> **Estado:** Plan (NO codeado). Creado 2026-09-01. Deriva de `prds/carta-qr-autopedido.prd.md` y sucede a `carta-qr-fase-2.plan.md` (✅ completa A–E).
> **Objetivo:** el comensal paga su cuenta desde el celu, escaneando el mismo QR de la mesa. Reusa el motor de cobro real (`RegisterPayment` + gateway + webhook) — la orden llega a `PAID` sola, sin cajero.
> **Por qué ahora:** F1 dejó la carta, F2 el autopedido; F3 cierra el loop de plata (pedir → comer → pagar, todo desde el teléfono).

## Insight de arquitectura (lo que hace esta fase barata… y lo que la hace delicada)

Al mapear el código, **el motor de cobro ya existe entero** y es reusable:

1. **`RegisterPayment` + `_settle_order` ya cobran una orden.** `RegisterPayment.execute(tenant_id, order_id, method, amount, tip, tax)` construye el `Payment(INFLOW, PENDING)`, llama `gateway.charge()` y luego `_settle_order` marca `PAID` cuando la suma de INFLOWs confirmados cubre `order.total()`. Los pagos **parciales ya funcionan** (varios `RegisterPayment` acumulan) → **dividir la cuenta es emergente**, no hay que inventar un motor.
2. **El gateway online ya está.** `MercadoPagoGateway.charge()` resuelve el **token del propio tenant**, crea la preferencia con `external_reference="<tenant_id>:<payment_id>"`, y devuelve el `Payment` **PENDING** con `checkout_url` (a dónde mandar al comensal). El **webhook** `POST /webhooks/mercadopago` → `ConfirmGatewayPayment` confirma y dispara `_settle_order`. Todo eso **se reusa tal cual** — el flujo público solo inicia el charge; la confirmación ya está resuelta.
3. **El token de F1 es el scope.** `HmacTableQrToken.verify(token) → (tenant_id, table_id)`. El molde exacto es `SubmitCustomerOrder` (F2): verificar token → `tenant_context.set` → gate de config → reusar casos de uso reales.
4. **La propina ya cabalga en el `Payment`** (`tip_amount`, arriba del `amount`) y entra sola al arqueo. El comensal puede dejar propina en el charge online sin infra nueva.

### Lo que hace la fase delicada (los gaps reales a construir)

1. **El pagador público solo tiene `tenant_id + table_id` — NO tiene `order_id`.** Y **no existe** `OrderRepository.list_by_table`/`by_session`. Hay que agregar un **read path**: "la cuenta de esta mesa" = las órdenes abiertas de la sesión del floor (`TableSessionRepository.get_open_by_table` → órdenes con ese `session_id`). **Es la pieza que falta.** (Hoy las órdenes llevan `session_id` pero nada las busca por él.)
2. **El cobro de hoy asume cajero autenticado.** `RegisterPayment` estampa `cash_session_id` de `cash.get_open` y puede fallar con `NoOpenCashSession` si el tenant lo exige; además el endpoint exige rol `CASHIER/MANAGER/OWNER`. Un pago del comensal ocurre **sin caja abierta y sin cajero** → el flujo público tiene que **relajar la política de caja** (pasar `cash=None`/`policy=None`) y ser **token-scoped, sin rol**.
3. **Online = asincrónico.** `charge()` devuelve PENDING + `checkout_url`; la orden llega a PAID **solo por el webhook**. El front público **redirige a MP y luego pollea** el estado. **Prerrequisito de deploy:** `PAYMENT_GATEWAY=mercadopago` + tenant con MP conectado + `MP_NOTIFICATION_URL`. El default es `manual` (confirma al toque, **sin `checkout_url`**) → sirve para dev/tests, no para un pago real remoto.
4. **Sin idempotencia ni monto de confianza.** `POST …/payments` no tiene idempotency key → un doble-tap del comensal crea dos charges. El flujo público **calcula el monto en el server** (nunca lo confía del cliente, igual que F2 manda solo ids) y agrega una **idempotency key**.
5. **`PaymentGatewayNotConnected`** se levanta hondo en el resolver → el endpoint público lo **muestra prolijo** ("el local no tiene pagos online; pagá con el mozo"), no un 500.
6. **Balance due no es de primera clase.** Se calcula ad hoc en `_settle_order` (`paid = Σ INFLOW confirmados`). El read path del punto 1 expone **total / pagado / saldo**.

---

## Defaults asumidos (confirmables — ver "Decisiones abiertas")
- **Pagar-DESPUÉS** (dine-in): el comensal paga la cuenta **acumulada de su mesa** (pidió, comió, paga). NO pay-before.
- **Paga la cuenta de la MESA entera** (todas las órdenes abiertas de la sesión), no "solo lo mío". Dividir = Tanda D.
- **Solo métodos online** en el flujo público (MercadoPago/QR); efectivo no tiene sentido remoto. Sin MP conectado → la carta muestra "pagá con el mozo" (degradado, sin romper).
- **Pagar cierra la orden solo** (vía `_settle_order`/webhook); la mesa se libera cuando todas sus órdenes quedan PAID (lógica de floor existente). Sin gate de mozo (la plata ya entró).
- **Propina opcional** en la pantalla de pago (presets %); cabalga en `Payment.tip_amount`.
- **Factura**: NO en el MVP (requiere doc_type/doc_number del comensal); gancho para después.

---

## Backend (`backend/`)

Arquitectura de siempre. Reusa `payment` (motor+gateway+webhook), `public_menu` (token), `order`, `table_session`, realtime.

1. **Read path "cuenta de la mesa"** (el gap principal):
   - `OrderRepository.list_open_by_session(tenant_id, session_id)` (o `list_open_by_table`) + adapter en `order_repo.py`. Filtra órdenes no PAID/CANCELLED de la sesión abierta del floor.
   - Caso de uso `GetTableBill(token)`: verifica token → `get_open_by_table` → junta las órdenes → devuelve **DTO**: ítems (nombre, cantidad, unit_price, modificadores), **total**, **pagado** (`Σ INFLOW confirmados` vía `payments.list_by_order`), **saldo**, `currency`, y **`online_pay_available`** (si el tenant tiene MP conectado + `self_pay_enabled`).
   - Endpoint público `GET /public/table/bill?token=` (sin auth). Solo lectura, sin plata → tanda de fundación segura.
2. **Config del tenant** `self_pay_enabled` (espeja `self_order_enabled` de F2: flag en `tenants`, default **off**). `GET/PUT /self-pay/settings` (OWNER/MANAGER). Migración chica.
3. **Caso de uso público `PayTableBill`** (`application/payment/` o `application/order/`):
   - `execute(token, tip=0, amount=None, idempotency_key)`: verifica token → gate `self_pay_enabled` (`SelfPayDisabled` 409) → resuelve la(s) orden(es) de la mesa → **monto = saldo calculado en el server** (o el parcial de Tanda D) → **reusa `RegisterPayment` con la política de caja relajada** (`cash=None`, sin `NoOpenCashSession`), `method=MERCADOPAGO` → `gateway.charge()` → devuelve `{ payment_id, status, checkout_url|null }`.
   - **Idempotencia**: guardar/consultar por `idempotency_key` (evita doble charge por doble-tap). Puede ser el `external_ref` o una columna nueva.
   - Si `PaymentGatewayNotConnected` → 409 `payment_gateway_not_connected` (el front lo muestra prolijo).
   - **La confirmación NO se toca**: el webhook (`ConfirmGatewayPayment`) ya marca PAID. Reusar.
   - **Multi-orden**: si la mesa tiene varias órdenes, el MVP puede cobrar **una preferencia por el total** atándola a una orden "ancla" y liquidando las demás, **o** (más simple y correcto) un charge por orden. Sub-decisión de implementación (arranca por 1 orden = 1 charge; la cuenta de mesa suma las órdenes en el front).
4. **Estado del pago (poll)** `GET /public/table/payment/{payment_id}?token=`: devuelve `status` (PENDING/CONFIRMED/FAILED) para que el front sepa cuándo mostrar "pagado". Token-scoped (el payment es del tenant del token).
5. **Realtime**: al confirmar (webhook), emitir `floor.changed` (ya lo hace `_settle_order`) → el mozo ve la mesa pagándose sola.
6. **Tests (80%+)**: bill arma total/pagado/saldo; `PayTableBill` con gateway fake confirma y marca PAID; con `manual` confirma al toque; sin MP conectado → 409; monto server-side (ignora el del cliente); idempotency key no duplica; token de otra mesa/tenant aislado; propina cabalga y entra al arqueo.

## Frontend (`frontend/`)

1. **Pantalla "Pagar"** en la carta pública (extiende `public-menu-page`): botón "Pagar" (o reemplaza "Pedir la cuenta" cuando hay `online_pay_available`) → pantalla con **la cuenta** (ítems + total + saldo), **selector de propina** (0/10/15% presets), y "Pagar $X".
2. **Redirect + poll**: `POST /public/table/pay` → si `checkout_url`, redirige a MP; al volver (o en un `GET payment/{id}` que pollea), muestra **"¡Pagado! 🎉"**. Reusa el patrón de estados de la carta.
3. **Degradado**: sin `online_pay_available`, la carta mantiene "Pedir la cuenta" (F1) — nada de pago online.
4. **Lado dueño — config**: toggle "Cobro desde la mesa" en `/app/mesas-qr` (junto al de autopedido de F2), contra `GET/PUT /self-pay/settings`. Un aviso si MP no está conectado (link a conectar).
5. **Split (Tanda D)**: elegir "pagar todo / pagar mi parte / pagar $X"; parciales acumulan (el motor ya lo soporta).

## Validación (gates del proyecto)
- Backend: `poetry run pytest` (80%+ en casos nuevos) + `ruff`. Gateway **fake/manual** en tests (nunca pega a MP real).
- Frontend: `npm run build` + `lint` + tests (gate real = `build`).
- Multi-tenant: token de una mesa NO paga la de otra; **monto server-side** (un pago manipulado NO cambia el saldo).
- Paridad: `self_pay_enabled` off → la carta se comporta EXACTO que en F2 (sin pago online). El cobro del cajero (endpoint autenticado) **no se toca**.

## Riesgos / notas
- **Plata real + asincronía**: el estado autoritativo es el **webhook**, no la respuesta del `charge`. El front nunca da por pagado sin el `status=CONFIRMED`. Idempotencia obligatoria.
- **Doble pago / carrera con el cajero**: nada impide hoy pagar de más o que el mozo cobre a la vez. Mitigar: monto = saldo server-side + idempotency key; el `_settle_order` ya es idempotente para el PAID.
- **Prerrequisito de prod**: `PAYMENT_GATEWAY=mercadopago` + tenant conectado + `MP_NOTIFICATION_URL`. Con `manual` (default) el flujo confirma al toque (bueno para dev/demo, sin checkout real).
- **Factura del comensal**: fuera del MVP (doc del cliente + `IssueInvoice`, que exige orden PAID — encaja después del pago). Gancho para una tanda futura.
- **Reabrir una orden pagada**: el guard `order_has_authorized_invoice` ya protege lo facturado; reabrir un pago del comensal reusa el reverso existente.

## Troceo sugerido (tandas)
- **A — Read path "cuenta de la mesa" (backend):** `list_open_by_session` + `GetTableBill` + `GET /public/table/bill`. Solo lectura (total/pagado/saldo + `online_pay_available`). Fundación segura, sin plata.
- **B — Pago público (backend):** config `self_pay_enabled` + `PayTableBill` (token-scoped, cobro relajado, monto server-side, idempotency) reusando `RegisterPayment`/gateway + `POST /public/table/pay` + `GET /public/table/payment/{id}`. El webhook ya confirma.
- **C — Pago público (frontend):** pantalla de pago (cuenta + propina) → redirect MP → poll → "pagado"; toggle de config del dueño. **A+B+C = pagar la cuenta entera desde el celu (MVP).**
- **D — Dividir la cuenta:** pagar parcial (mi parte / $X / por N); parciales acumulan. UI + (opcional) helper de reparto.
- **(Futuro) E — Factura del comensal:** pedir factura tras pagar (doc → `IssueInvoice`).

Cada tanda cierra con sus gates. A→C es el MVP del pago desde la mesa; D agrega el reparto.

---

## Decisiones abiertas (confirmar antes de implementar)
Con defaults ya elegidos (arriba), pero conviene confirmar:
1. **Pagar-después + cuenta de la mesa entera** (no "solo lo mío") para el MVP. ¿OK?
2. **Solo pago online** (MercadoPago) en la carta; sin MP conectado → "pagá con el mozo". ¿OK, o querés también "avisar que pago en efectivo con el mozo" como acción?
3. **Propina en la pantalla de pago** (presets %). ¿Qué presets (0/10/15/20)? ¿Va al MVP o se difiere?
4. **Dividir la cuenta**: ¿va como Tanda D del MVP o se difiere a una fase aparte? (El motor ya lo soporta; es UI + un monto parcial.)
5. **Factura para el comensal**: ¿se difiere (recomendado) o entra?

## Próximo
Aprobar este plan (y las 5 decisiones) → `/prp-implement` por tandas (A→D). Al terminar F3, la Carta QR cierra el loop completo (ver → pedir → pagar). Posibles siguientes: factura del comensal, o loyalty/CRM del comensal (identificación opcional que quedó como gancho en F2).
