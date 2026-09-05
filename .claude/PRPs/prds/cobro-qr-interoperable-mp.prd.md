# Cobro presencial con QR interoperable de Mercado Pago

## Problem Statement

Hoy el local que usa Wellnod cobra por fuera de la app: el mozo/cajero abre la maquinita (posnet) o la app de Mercado Pago aparte, cobra, **y recién ahí "anota" el pago a mano** en el cobro (el chip "QR" del cobro es un registro manual, no cobra nada). Eso deja al menos tres agujeros: (1) la plata pasa por un riel que **le cuesta comisión al local** (posnet) y por el que **la plataforma no participa**; (2) el pago **no se concilia solo** — depende de que alguien lo cargue bien; (3) no hay forma de que Wellnod **monetice el flujo de pagos** que ya está intermediando operativamente.

## Evidence

- **El chip "QR" del cobro es manual hoy:** en `mobile/lib/features/cashier/cobro_sheet.dart` los métodos son `cash/card/transfer/qr` (`_methods`, L26-33) y `_register` (L166) solo **registra** un pago; el comentario del archivo lo dice explícito: *"El cobro real online (MercadoPago) queda para la Carta QR del comensal"* (L15). Si viene `checkout_url`, la app apenas tostea *"MercadoPago: cobrar online por la Carta QR"* (L182-183).
- **El puerto de pago ya contempla un gateway QR:** `backend/app/domain/payment/ports.py:14` — *"MercadoPago / QR / Payway adapters slot in"*; y `entities.py` deja `checkout_url` justamente para *"redirect the payer to a checkout link / render a QR"*.
- **`PaymentMethod.QR` ya existe** en el dominio (`backend/app/domain/payment/value_objects.py:18`).
- **El motor pesado ya está construido** (lo usa la Carta QR del comensal): `RegisterPayment` + `PaymentGateway` port + `ConfirmGatewayPayment` (webhook) + idempotencia (`repository.py:37`, `entities.py:46`) + conexión **OAuth por tenant** en `payment_credentials`.
- **Contexto regulatorio (habilitante):** por norma del BCRA (**Transferencias 3.0**), en Argentina **todo QR es interoperable** — un QR de Mercado Pago se paga desde MODO, apps de banco o cualquier fintech. O sea "cualquier billetera lo paga" **sale por regulación**, sin programa especial.
- **La comisión NO es un campo de código en el flujo QR:** la Orders API de MP **no tiene `marketplace_fee`/`application_fee`**; la atribución de comisión va por `integration_data.integrator_id` / `platform_id` / `sponsor.id`, **asignados por Mercado Pago** (alta de integrador, trámite comercial).

## Proposed Solution

Que el mozo/cajero **genere desde la app un QR dinámico de Mercado Pago** por el monto de la cuenta, se lo muestre al comensal, éste lo pague con **la billetera que quiera** (interoperable) y **MP confirme por webhook** → el pago se marcha solo y baja el "Restante". Reusamos el motor de pagos existente detrás del `PaymentGateway` port (nuevo adapter **Orders-QR** de MP) y el webhook que ya tenemos. El **método "QR" del cobro se vuelve polimórfico**: el **tenant elige en Ajustes** si su "QR" es **"QR de MP"** (cobra de verdad) o **"QR por afuera"** (registro manual, como hoy); el **mozo ve siempre el mismo chip**, cambia sólo qué hace según la config. Lanzamos **sin comisión** (la parte técnica no depende de MP) y **prendemos la comisión después**, cuando MP nos asigne el `integrator_id` — el alta de integrador corre en paralelo.

## Key Hypothesis

Creemos que **dejar cobrar por QR interoperable desde la propia app (sin posnet), con confirmación automática**, va a **bajar el costo de cobro del local, conciliar los pagos solos y abrir el riel de monetización de la plataforma** para **dueños de PyMEs de hospitality y para Wellnod**.
Sabremos que acertamos cuando **una parte medible de los cobros pase por el QR de la app, la conciliación sea automática (cero carga manual en esos pagos), y —una vez activo el integrador— cada pago QR deje una comisión para la plataforma**.

## What We're NOT Building

- **`marketplace_fee` en el flujo QR** — MP no lo expone ahí; la comisión va por alta de integrador (`integration_data`).
- **Convertirnos en agregador/procesador propio (Payfac)** — fuera de alcance; usamos el riel de MP.
- **Cobro por QR en la Carta QR web del comensal (v1)** — el comensal sigue con su pago online actual (Checkout Pro); acá el alcance es **cobro presencial en la app**.
- **MP Point / maquinita física** — es otra API (hardware); no en este PRD.
- **Flujo aceptador de crédito interoperable (homologación con `coelsa_id`)** — capa extra opcional/futura; el caso base (transferencia/débito) ya funciona por Transferencias 3.0.
- **Reemplazar el registro manual** — el "QR por afuera" sigue disponible para el que no conecta MP.

## Success Metrics

| Metric | Target | How Measured |
|--------|--------|--------------|
| Cobros que pasan por el QR de la app | ≥ 30% de las órdenes de locales con MP-QR activo | % pagos `method=QR` con gateway MP vs total |
| Conciliación automática | 100% de los pagos QR-MP | pagos confirmados por webhook / pagos QR-MP |
| Tiempo "generar QR → confirmado" | < 60 s (p50) | delta creación de la orden MP → webhook |
| Comisión capturada (post-integrador) | > 0 y creciente | suma de comisión atribuida por `integrator_id` |
| Tenants con MP-QR configurado | crecimiento MoM | % tenants con `qr_payment_mode=mp_dynamic` |

## Open Questions

- [x] **RESUELTA:** el flujo **OAuth tenant↔MP YA existe** y completo — `ConnectMercadoPago` (`application/payment/connect_mercadopago.py`) + adapter `mercadopago_oauth.py`, `GET /integrations/connect` (URL de autorización) + `GET /integrations` (estado), credenciales en `payment_credentials` (`credentials_repo.py` + `credentials_resolver.py`), gateway MP operativo (`mercadopago_gateway.py`). La Fase 1 lo **reusa**; sólo son nuevos el adapter Orders-QR, el provisioning store/POS y el mapeo del webhook.
- [ ] Confirmación en la app: ¿**push/SSE** desde el webhook (recomendado) o **polling** a `GET /v1/orders/{id}` mientras el QR está en pantalla?
- [ ] TTL del QR dinámico y manejo de expiración/cancelación (`POST /v1/orders/{id}/cancel`) si el cliente no paga.
- [ ] Modelo de negocio de la comisión: ¿% fijo, quién la absorbe (local vs comensal), mínimos? — **input del negocio, no bloquea la técnica**.
- [ ] Split parcial: ¿se puede generar un QR por una **parte** de la cuenta (dividir) o sólo por el restante total? (El motor ya soporta parciales.)

---

## Users & Context

**Primary User**
- **Who**: el **mozo/cajero** de un restaurante PyME (roles `WAITER`/`CASHIER`) cobrando en la mesa o en la caja, con el celular en la mano. Secundario: el **dueño** (`OWNER`/`MANAGER`) que configura el modo de cobro QR.
- **Current behavior**: cobra con **posnet** o abriendo la app de MP por separado, y después **carga el pago a mano** en el cobro de Wellnod.
- **Trigger**: la cuenta está lista para cobrar y el cliente quiere pagar con billetera/QR.
- **Success state**: toca "QR" en el cobro → aparece el QR → el cliente lo escanea con su billetera → **el pago se confirma solo** y baja el "Restante", sin cargar nada a mano.

**Job to Be Done**
Cuando **el cliente quiere pagar con su billetera**, quiero **mostrarle un QR desde la app y que el pago se confirme solo**, para **cobrar sin posnet, sin conciliar a mano, y (para Wellnod) capturar una comisión del pago**.

**Non-Users**
El comensal de la Carta QR web (sigue con su pago online actual). La cocina/barra. El local que **no** conecta MP (usa el "QR por afuera" manual como hoy).

---

## Solution Detail

### Core Capabilities (MoSCoW)

| Priority | Capability | Rationale |
|----------|------------|-----------|
| Must | Adapter **Orders-QR de MP** detrás del `PaymentGateway` port (crear orden dinámica, traer string del QR, cancelar) | Es el corazón técnico; respeta ports&adapters |
| Must | **Provisionar store + POS** por tenant (con su token OAuth) | MP exige caja/POS para el QR dinámico |
| Must | **Enganchar el webhook** de la orden QR a `ConfirmGatewayPayment` | Confirmación automática reusando el motor |
| Must | **Chip "QR" polimórfico** según `qr_payment_mode` del tenant | Mismo chip para el mozo; comportamiento según config |
| Must | **Render del QR** en el cobro + espera de confirmación → baja "Restante" | La UX del cobro presencial |
| Must | **Selector en Ajustes**: "QR de MP" vs "QR por afuera (manual)" | El dueño elige; default = manual (sin setup) |
| Should | **Cancelación / TTL** del QR si no se paga | Evitar QRs colgados / cobros fantasma |
| Should | **Alta de integrador** + `integration_data.integrator_id` en la orden | Activa la comisión de la plataforma |
| Could | Confirmación por **push** al cajero (app en background) | Pulido sobre el SSE/polling |
| Could | **Flujo aceptador de crédito interoperable** (homologación `coelsa_id`) | Extiende a crédito de billeteras externas |
| Won't | `marketplace_fee` en QR; Payfac propio; QR en la carta web; MP Point | Fuera de alcance (ver "NOT Building") |

### MVP Scope

**Fase 1 + 2**: el mozo, en un local con **MP conectado** y `qr_payment_mode=mp_dynamic`, toca "QR" en el cobro → la app pide al backend crear la **orden dinámica** → muestra el **QR** → el cliente paga con cualquier billetera → el **webhook** confirma → baja el "Restante". **Sin comisión todavía.** Es la mínima prueba de que "se puede cobrar por QR interoperable desde la app y conciliar solo".

### User Flow

- **Tenant "QR por afuera" (default, sin MP):** mozo toca "QR" → **registro manual** (idéntico a hoy). Cero cambios para quien no conecta MP.
- **Tenant "QR de MP" (MP conectado):** mozo toca "QR" → app crea la orden dinámica (por el restante o un parcial) → **muestra el QR** → cliente escanea con **su billetera** → paga → MP → **webhook** → `ConfirmGatewayPayment` → el pago aparece en la lista y baja el "Restante". Si no paga en el TTL, el QR se cancela.
- **Con integrador activo:** igual que arriba, pero la orden lleva `integration_data.integrator_id` → MP **liquida la comisión** a la cuenta de la plataforma; el resto queda en la cuenta del local.

---

## Technical Approach

**Feasibility**: **MEDIUM-HIGH**. El motor de pago (registro + gateway port + webhook + idempotencia + OAuth por tenant) **ya existe** (lo usa la Carta QR). Lo nuevo es el **adapter Orders-QR**, el **provisioning store+POS** y el **render/espera** en la app. La comisión es **trámite comercial** (no técnico) y no bloquea el lanzamiento.

**Architecture Notes**
- **Nuevo adapter en `infrastructure`** detrás del `PaymentGateway` port (mismo patrón que el gateway actual): `POST /v1/orders` con `config.qr.mode: dynamic` → devuelve el string del QR; `GET /v1/orders/{id}` (consulta); `POST /v1/orders/{id}/cancel`.
- **Provisioning por tenant**: `POST /users/{user_id}/stores` + `POST /v2/pos` con el **access_token del tenant** (obtenido por OAuth). Guardar `store_id`/`pos_id` junto a `payment_credentials`. Idempotente (crear una vez por tenant).
- **Webhook**: mapear la notificación de la orden QR a `ConfirmGatewayPayment` (ya confirma pagos de gateway). Multi-tenant: resolver el tenant por el `collector`/`external_reference`.
- **`qr_payment_mode`** = setting por tenant (`mp_dynamic` | `external`), default `external`. El chip "QR" del cobro deriva su comportamiento de este flag (mismo patrón "modo con nombre" de la Carta QR). El backend valida que `mp_dynamic` sólo se pueda activar con MP conectado + store/POS listos.
- **Comisión**: `integration_data.integrator_id` (prefijo `dev_`, **asignado por MP**) en el body de la orden. Se cablea en Fase 4; sin él, se cobra igual pero sin comisión.
- **Confirmación en la app**: reusar SSE/realtime o polling a la orden mientras el QR está en pantalla (decisión abierta).
- Multi-tenant: toda query/registro filtra por `tenant_id`; el QR y el pago se atan a la orden y al tenant correctos.

**Technical Risks**

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| El tenant no tiene MP conectado (aún) | Baja | El flujo OAuth YA existe (`GET /integrations/connect` + `payment_credentials`); default `external` no lo exige; el gate de Fase 3 guía a conectar |
| Provisioning store+POS falla o duplica | Media | Idempotencia por `external_id`; crear una vez y cachear `store_id/pos_id` |
| Webhook de la orden QR distinto al de pagos actuales | Media | Adapter mapea el evento a `ConfirmGatewayPayment`; tests con notificaciones reales |
| Comisión bloqueada por el alta de integrador | Alta (comercial) | Lanzar sin comisión; `integrator_id` se cablea cuando MP lo asigna, sin retocar el flujo |
| QR colgado si el cliente no paga | Media | TTL + `cancel`; el "Restante" no baja hasta el webhook confirmado |
| Homologación de MP antes de producción | Media | Correr `integration-quality`; entorno de prueba primero (`APP_USR` de test) |

---

## Implementation Phases

<!--
  STATUS: pending | in-progress | complete
  PARALLEL: phases that can run concurrently
  DEPENDS: phases that must complete first
  PRP: link to generated plan file once created
-->

| # | Phase | Description | Status | Parallel | Depends | PRP Plan |
|---|-------|-------------|--------|----------|---------|----------|
| 1 | Fundaciones MP Orders-QR (backend) | Adapter Orders-QR detrás del gateway port (crear/consultar/cancelar orden dinámica) + provisioning store+POS por tenant + mapeo del webhook a `ConfirmGatewayPayment` + setting `qr_payment_mode` | in-progress | - | - | `.claude/PRPs/plans/cobro-qr-fundaciones-backend.plan.md` |
| 2 | Cobro con QR en la app (mobile) | Chip "QR" polimórfico según `qr_payment_mode`; generar → **render del QR** → esperar confirmación (SSE/polling) → baja "Restante"; cancelación/TTL | pending | with 3 | 1 | - |
| 3 | Config del modo QR por tenant (Ajustes) | Selector "QR de MP" vs "QR por afuera" en Ajustes; garantizar MP conectado (OAuth) + store/POS antes de permitir `mp_dynamic` | pending | with 2 | 1 | - |
| 4 | Alta de integrador + comisión | Onboarding de la plataforma como integrador con MP → `integrator_id`; cablear `integration_data.integrator_id` en la orden → activa la comisión | pending | with 2, 3 | 1 | - |
| 5 | Homologación + crédito interoperable (opcional) | `integration-quality` + flujo aceptador de crédito (6 tests con `coelsa_id`) — extiende a crédito de billeteras externas | pending | - | 4 | - |

### Phase Details

**Phase 1: Fundaciones MP Orders-QR (backend)**
- **Goal**: poder crear un QR dinámico de MP por una orden y que su pago se confirme solo, reusando el motor.
- **Scope**: adapter Orders-QR (`POST /v1/orders` dynamic / `GET` / `cancel`) detrás del `PaymentGateway` port; provisioning `stores` + `pos` por tenant con su token; mapeo del webhook de la orden QR a `ConfirmGatewayPayment`; setting `qr_payment_mode` (default `external`). **Sin comisión.**
- **Success signal**: en entorno de prueba, crear una orden QR devuelve un string de QR; un pago de prueba dispara el webhook y marca el pago confirmado por la vía existente.

**Phase 2: Cobro con QR en la app (mobile)**
- **Goal**: que el cajero cobre por QR desde el cobro y vea el "Restante" bajar solo.
- **Scope**: el chip "QR" deriva su comportamiento de `qr_payment_mode`; en `mp_dynamic` genera la orden, **renderiza el QR** en pantalla, espera la confirmación (SSE/polling) y actualiza el cobro; manejo de cancelación/TTL; en `external`, comportamiento manual actual intacto.
- **Success signal**: con un local de prueba en `mp_dynamic`, el mozo genera el QR, se paga, y el pago aparece en la lista sin carga manual.

**Phase 3: Config del modo QR por tenant (Ajustes)**
- **Goal**: que el dueño elija su modo de cobro QR sin tocar flags técnicos.
- **Scope**: selector "QR de MP / QR por afuera" en Ajustes; gate: `mp_dynamic` sólo si MP está conectado (OAuth) y el store/POS existe (si no, guiar a conectar).
- **Success signal**: cambiar el modo en Ajustes cambia qué hace el chip "QR" del cobro para ese tenant.

**Phase 4: Alta de integrador + comisión**
- **Goal**: capturar la comisión de la plataforma por cada pago QR.
- **Scope**: trámite de alta de integrador/partner con MP (obtener `integrator_id`); cablear `integration_data.integrator_id` en la creación de la orden; verificar la liquidación de la comisión.
- **Success signal**: un pago QR de prueba deja una comisión atribuida a la cuenta de la plataforma; el resto va al local.

**Phase 5: Homologación + crédito interoperable (opcional)**
- **Goal**: habilitar que billeteras externas paguen el QR con **crédito** (más allá de la interoperabilidad de transferencia/débito).
- **Scope**: `integration-quality`; incorporación al flujo aceptador; 6 escenarios con `coelsa_id` como evidencia.
- **Success signal**: MP aprueba la homologación; pagos con crédito desde billeteras externas confirmados.

### Parallelism Notes

Las **Fases 2 y 3** (mobile + Ajustes) pueden ir en paralelo una vez lista la **Fase 1**. La **Fase 4 (comisión)** es un **track comercial** que corre en paralelo a 2–3: técnicamente es cablear un ID, pero depende del alta con MP; por eso lanzamos sin comisión y la prendemos cuando llega. La **Fase 5** es opcional y posterior a 4.

---

## Decisions Log

| Decision | Choice | Alternatives | Rationale |
|----------|--------|--------------|-----------|
| Riel del QR | **QR interoperable de MP (Transferencias 3.0)** | Payfac propio; agregador; Geopagos | Reusa MP + el motor existente; interoperable por norma; sin construir procesador |
| Alcance v1 | **Cobro presencial en la app** | Sumar la Carta QR web del comensal | Foco; la carta ya tiene pago online (Checkout Pro) |
| Comisión vs lanzamiento | **Lanzar sin comisión, prenderla después** | Esperar el alta de integrador | La técnica no depende de MP; no bloquear el valor |
| Mecanismo de comisión | **`integration_data.integrator_id`** (alta de integrador) | `marketplace_fee` (no existe en QR) | Es el único camino que expone MP para el flujo QR |
| Método "QR" del cobro | **Chip único polimórfico por `qr_payment_mode`** (MP vs manual), elegido por el tenant | Dos chips separados; reemplazar el manual | El mozo ve lo mismo; el dueño decide; no rompe a quien no conecta MP |
| Default del modo | **`external` (manual)** | `mp_dynamic` por default | No exige setup MP; se opta-in |
| Confirmación del pago | **Reusar `ConfirmGatewayPayment` vía webhook** | Confirmar a mano; polling puro | Ya concilia pagos de gateway; automático |
| API de QR | **Orders API (`/v1/orders` dynamic)** | Legacy `/instore/orders/qr/...` | Es el camino moderno unificado de MP |

---

## Research Summary

**Market Context**
- En Argentina, por norma del BCRA (**Transferencias 3.0**, plena interoperabilidad), **cualquier billetera** (MP, MODO, apps de banco, fintech) paga el QR de cualquier comercio; desde abril 2025 se sumó débito a transferencia/crédito/prepagas. → "cualquiera lo paga" **sale por regulación**, sin programa especial.
- MP es el mayor **aceptador** del sistema (>1,3M de QR desplegados); cobrar por QR creció fuerte tras Transferencias 3.0.
- El **posnet** le cuesta comisión al local; el **QR interoperable (transferencia)** es mucho más barato → palanca de valor para el local y de monetización para la plataforma.

**Technical Context**
- La **Orders API** de MP genera el QR dinámico: `POST /v1/orders` (`config.qr.mode: dynamic`), `GET /v1/orders/{id}`, `POST /v1/orders/{id}/cancel`.
- Setup por comercio: **store** (`POST /users/{user_id}/stores`) + **POS/caja** (`POST /v2/pos`); OAuth del vendedor (`auth.mercadopago.com/authorization` → `/oauth/token` → `access_token` 180 días + `refresh_token`).
- La **comisión** NO es `marketplace_fee` en QR: va por `integration_data.integrator_id`/`platform_id`/`sponsor.id`, **asignados por MP** (alta de integrador con Soporte).
- El repo ya tiene: `PaymentGateway` port con hueco para "MercadoPago / QR" (`domain/payment/ports.py:14`), `ConfirmGatewayPayment` (webhook), idempotencia, OAuth por tenant (`payment_credentials`), y el chip "QR" manual en el cobro (`cobro_sheet.dart`).

**Fuentes**
- MP Docs — QR Code Overview (modelos estático/dinámico/interoperable): https://www.mercadopago.com.ar/developers/es/docs/qr-code/overview
- MP Docs — crear aplicación QR / store & POS: `/qr-code/create-application`, `/qr-code/create-store-and-pos`
- MP Docs — OAuth (vincular cuenta del vendedor): `/security/oauth/creation`
- MP Docs — Orders API QR dinámico + `integration_data` (integrator/platform/sponsor)
- BCRA Transferencias 3.0 / QR interoperable: Cámara Fintech, El Cronista, Portal FinDev

---

*Generated: 2026-09-04*
*Status: DRAFT - needs validation*
