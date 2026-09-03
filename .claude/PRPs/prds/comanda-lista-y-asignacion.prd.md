# Comanda lista + asignación de mozo (avisos operativos)

## Problem Statement

En un local de hospitality, el loop **mozo → cocina → mesa** hoy es **pasivo**: cuando la cocina termina un plato, el mozo solo se entera si mira el Piso — nadie lo empuja. Además, en el autopedido por QR la mesa queda **sin un mozo humano a cargo** (el pedido nace con `waiter_id` nulo). El costo de no resolverlo: platos que se enfrían esperando, mozos yendo a chequear la cocina, mesas "huérfanas" que nadie atiende, y —si se abre el autoservicio sin candado— pedidos falsos que llegan a la cocina sin pagar.

## Evidence

- **El estado "listo" ya existe pero no avisa nada:** el ciclo del ítem es `PENDING → SENT → PREPARING → READY → SERVED` (`backend/app/domain/order/value_objects.py:36-45`); `READY` = la cocina terminó, y no dispara ninguna notificación.
- **No hay (re)asignación de mozo:** `TableSession.waiter_id` (`backend/app/domain/table_session/entities.py:37`) se setea **una sola vez** al abrir (`table_session/use_cases.py:47-56`); el grep de `assign_waiter|reassign|set_waiter|claim_table` no arroja nada.
- **El pedido QR nace sin mozo real:** `SubmitCustomerOrder._resolve_waiter` devuelve el UUID nulo si no hay sesión con mozo (`backend/app/application/order/self_order.py:176-180`), marcado como `OrderSource.CUSTOMER_QR`.
- **No existe "pagar-primero":** `PayTableBill` cobra una orden **ya existente** al final y no toca la cocina (`backend/app/application/payment/pay_table_bill.py:84-151`); las settings de self-pay solo tienen `enabled` + `tips_enabled`.
- **Infra reutilizable ya presente:** SSE en vivo de Piso/KDS (`/realtime/{floor,kds}/stream`). **Push (APNs/FCM) NO está montado.**

## Proposed Solution

Que la app **avise sola** en el momento justo y garantice que **toda mesa tenga un mozo dueño**. Dos capacidades: (1) **"Comanda lista"** — al pasar la orden a `READY`, aviso + modal al mozo dueño con qué lleva y a qué mesa; (2) **Asignación de mozo** — por **confirmación** (QR modo Salón: el mozo que confirma queda dueño) o **automática** (QR modo Autoservicio: al pagar, se auto-asigna). El tenant **elige el modo de la Carta QR desde la UI** (Salón / Autoservicio / Solo lectura), con descripción; los flags técnicos se derivan del modo. Se prioriza reusar el **SSE existente** (aviso en vivo) antes que montar push, y las **dos barreras anti-abuso** (confirmación en Salón; pagar-primero en Autoservicio).

## Key Hypothesis

Creemos que **avisar proactivamente cuando la comanda está lista y garantizar un mozo dueño por mesa** va a **bajar el tiempo de servicio y eliminar las mesas sin atender** para **mozos y dueños de PyMEs de hospitality**.
Sabremos que acertamos cuando **el tiempo "listo → servido" baje de forma medible, ~100% de las mesas tengan mozo real asignado, y cero comandas sin pagar lleguen a la cocina en modo autoservicio.**

## What We're NOT Building

- **Geofencing / validar cercanía del comensal** — spoofeable y con costo de privacidad; la confirmación y el pagar-primero ya cubren el abuso.
- **Token de QR rotativo** — el QR impreso es estático; rotarlo exige pantalla en la mesa (fuera de alcance).
- **Auto-asignación por sector (v1)** — arrancamos con round-robin; el mapeo mozo↔sector no existe hoy.
- **Notificaciones offline** — dependen de conexión; el Piso es el fallback pasivo.
- **Reemplazar el flujo del mozo real (Caso A)** — se le suma el aviso, no se cambia.

## Success Metrics

| Metric | Target | How Measured |
|--------|--------|--------------|
| Tiempo "listo → servido" | ↓ vs. baseline (ej. −30%) | delta `ready_at → served_at` del OrderItem |
| Mesas con mozo real asignado | ~100% (locales con autopedido) | % sesiones con `waiter_id` no nulo |
| Comandas no pagadas que llegan a cocina (Autoservicio) | 0 | órdenes marchadas sin pago confirmado |
| Adopción del aviso | ≥ 70% avisos abiertos | % `OrderReadyToServe` abiertos desde el aviso |
| Comandas servidas a tiempo | ≥ 90% dentro de X min de `READY` | histograma `ready→served` |

## Open Questions

- [ ] Auto-asignación (Caso C): ¿round-robin entre fichados (recomendado), pool puro, o por sector?
- [ ] Modo pagar-primero: ¿config global del local, o por mesa/sector?
- [ ] Autoservicio: ¿"una orden = un pago" (sin rondas), o el comensal pide en rondas y paga cada una?
- [ ] TTL de un `PENDING` sin confirmar (B) / sin pagar (C) antes de expirar.
- [ ] Reasignación: ¿solo el encargado, o cualquier mozo "toma" una mesa sin dueño?

---

## Users & Context

**Primary User**
- **Who**: el **mozo** de un restaurante PyME (rol `WAITER`), en plena operación de salón, con el celular en la mano. Secundario: el **dueño/encargado** que configura el modo de la Carta QR.
- **Current behavior**: camina hasta la cocina/KDS a chequear si su comanda está lista; mira el Piso para ver qué mesa "pide atención". En autopedido, nadie queda formalmente a cargo de la mesa.
- **Trigger**: la cocina termina un plato (`READY`); o un comensal hace un pedido por QR.
- **Success state**: le llega el aviso "Mesa X lista" con qué llevar, la sirve sin demoras; y cada mesa QR tiene un mozo dueño desde el arranque.

**Job to Be Done**
Cuando **la cocina termina mi comanda (o entra un pedido por QR a mi mesa)**, quiero **que la app me avise con qué llevar y a qué mesa (y que quede claro que la mesa es mía)**, para **servir rápido sin ir a chequear la cocina ni dejar mesas sin atender**.

**Non-Users**
La cocina/barra (`KITCHEN`/`BAR`) — ellos disparan el `READY` pero no reciben el aviso de servir. El comensal — no ve nada de asignación ni de avisos internos.

---

## Solution Detail

### Core Capabilities (MoSCoW)

| Priority | Capability | Rationale |
|----------|------------|-----------|
| Must | Evento `OrderReadyToServe` al pasar la orden a `READY` | Es el disparador central de la Idea 1 |
| Must | Aviso en vivo (SSE) + **modal** con la comanda al mozo dueño | Valor inmediato sin montar push |
| Must | Asignación al **confirmar** el pedido QR (Caso B) | Da dueño a la mesa + barrera anti-abuso |
| Must | Caso de uso **(re)asignar mozo** a la sesión | Cambios de turno / mesas huérfanas |
| Must | Modo **pagar-primero** + **auto-asignación** (Caso C) | Autoservicio seguro; asigna al pagar |
| Must | **Selector de modo de la Carta QR** en la UI (Salón/Autoservicio/Solo-lectura) con descripción | El tenant elige; oculta los flags crudos |
| Should | Bandeja **"pedidos QR por confirmar"** | Para que los mozos vean los `PENDING` de QR |
| Should | **Push real** (APNs/FCM) para app cerrada | Alcanzar al mozo con la app en background |
| Could | Sonido/haptic del aviso; "quién sirve" en el KDS; asignación por sector | Pulido / futuro |
| Won't | Geofencing; token rotativo; notificaciones offline | Fuera de alcance |

### MVP Scope

**Fase 1**: emitir `OrderReadyToServe` cuando la orden llega a `READY` y mostrarle al **mozo dueño** (con la app abierta, vía SSE) un **banner + modal** con la comanda y el nº de mesa. Sirve para los Casos A y B sin tocar pagos ni push. Es la mínima prueba de que "avisar proactivamente acelera el servicio".

### User Flow

- **Caso A (mozo, sin QR):** abre mesa → él es dueño → marcha → cocina "Listo" (`READY`) → **aviso + modal** al dueño → sirve.
- **Caso B (QR Salón, `requires_confirmation=ON`, pago al final):** comensal pide → `PENDING` → bandeja "QR por confirmar" → un mozo **confirma** (queda dueño + marcha) → cocina "Listo" → **aviso + modal** → sirve → paga al final.
- **Caso C (QR Autoservicio, `requires_confirmation=OFF` + pagar-primero):** comensal pide → orden retenida `PENDING` → **paga primero** → pago confirmado ⇒ marcha a cocina + **auto-asigna mozo** (round-robin/pool) + **push "te asignaron la Mesa X"** → cocina "Listo" → **aviso + modal** → lleva (ya pago).

---

## Technical Approach

**Feasibility**: **HIGH** para Fases 1–2 (el estado `READY`, el SSE y el `waiter_id` ya existen; solo falta cablear el evento y un caso de uso de asignación). **MEDIUM** para Fase 3 (pagar-primero invierte el ciclo: el pago pasa a habilitar la cocina) y Fase 4 (push es infra nueva).

**Architecture Notes**
- Reusar el **bus de realtime/SSE existente** para el aviso en vivo (Fase 1); no bloquear el valor esperando push.
- **Push como port `NotificationService`** + adapter APNs/FCM (mismo patrón ports&adapters que AFIP/LLM/pagos). Payload con `order_id`/`table_id` para deep-link al modal.
- **`AssignTableWaiter`** (nuevo caso de uso) como única vía de setear/actualizar `TableSession.waiter_id` (invocado desde confirmar-QR, reasignación y auto-asignación).
- **Pagar-primero**: la orden QR con `prepay_required=ON` **no marcha** al crearse; el **webhook de pago confirmado** dispara marcha + auto-asignación. Checkout **por-orden** (distinto del "pagar la cuenta" actual).
- **Modo de Carta QR** = preset nombrado en settings que deriva `requires_confirmation` + `prepay_required`; la UI solo muestra los modos con su descripción.
- Multi-tenant: todo evento/push filtra por `tenant_id` y va al `waiter_id` correcto.

**Technical Risks**

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Push (APNs/FCM) no está montado | Alta | Fase 1 usa SSE en vivo; push se aísla en un port en Fase 4 |
| Pagar-primero invierte el ciclo de la orden (pago→cocina) | Media | Reusar `PENDING` retenido; el webhook dispara la marcha; feature-flag por tenant |
| Auto-asignación injusta / mozo saturado | Media | Round-robin por menos-mesas-activas entre fichados; fallback a pool |
| Spam de `PENDING` QR sin confirmar/pagar | Media | TTL + límite por mesa; la confirmación/pago son la barrera |
| Deep-link del push al modal correcto | Baja | Payload con `order_id`; ruta directa al modal |

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
| 1 | Aviso "comanda lista" | Evento `OrderReadyToServe` + aviso en vivo (SSE) + modal en mobile (Casos A/B/C) | complete | - | - | `.claude/PRPs/plans/comanda-lista-aviso.plan.md` |
| 2 | Asignación por confirmación | Asignar al confirmar QR (B) + bandeja "QR por confirmar" + caso de uso (re)asignar mozo | complete | - | 1 | `.claude/PRPs/plans/comanda-asignacion-confirmacion.plan.md` |
| 3 | Modo Autoservicio (Caso C) | Selector de modo + pagar-primero (orden retenida + checkout por-orden + marcha por pago) + auto-asignación (round-robin/pool) + aviso "te asignaron" | complete | - | 2 | `.claude/PRPs/plans/autoservicio-prepay.plan.md` |
| 4 | Push real | Port `NotificationService` + adapter APNs/FCM + deep-link (app cerrada) — refuerza A/B/C | pending | - | 1 | `.claude/PRPs/plans/push-notifications.plan.md` |

### Phase Details

**Phase 1: Aviso "comanda lista"**
- **Goal**: que el mozo dueño se entere al instante de que la comanda está lista, sin ir a la cocina.
- **Scope**: emitir `OrderReadyToServe` en la transición a `READY`; SSE → banner + modal (ítems/modif./notas/mesa) + botón "Servido"; funciona para A y B (y luego C).
- **Success signal**: con la app abierta, al marcar "Listo" en el KDS, al mozo dueño le aparece el modal < 2 s.

**Phase 2: Asignación por confirmación**
- **Goal**: que toda mesa QR modo Salón tenga un mozo dueño y una barrera humana anti-abuso.
- **Scope**: al confirmar (marchar) un pedido QR `PENDING`, asignar el `waiter_id`; bandeja "QR por confirmar"; caso de uso `AssignTableWaiter` (+ reasignación manual).
- **Success signal**: un pedido QR confirmado deja la sesión con `waiter_id` = el mozo que confirmó; una mesa huérfana se puede reasignar.

**Phase 3: Modo Autoservicio (Caso C)**
- **Goal**: habilitar autoservicio seguro (sin pago no hay comanda) con mozo auto-asignado.
- **Scope**: selector de modo en Ajustes; `prepay_required`; orden retenida; checkout por-orden; webhook de pago ⇒ marcha + auto-asignación (round-robin/pool); aviso "te asignaron".
- **Success signal**: un pedido QR autoservicio solo llega a cocina tras pago confirmado, con un mozo asignado y notificado.

**Phase 4: Push real**
- **Goal**: alcanzar al mozo aunque tenga la app cerrada/en background.
- **Scope**: port `NotificationService` + adapter APNs/FCM; registro de device token; deep-link al modal; permisos.
- **Success signal**: con la app cerrada, el aviso "Mesa X lista" / "te asignaron" llega como push y abre el modal correcto.

### Parallelism Notes

La **Fase 4 (push)** puede ir en paralelo a las Fases 2–3: depende solo de la Fase 1 (el evento ya emitido) y aísla la infra de notificaciones en un port. Las Fases 2 y 3 son secuenciales (C se apoya en el concepto de "mozo dueño" que consolida la Fase 2).

---

## Decisions Log

| Decision | Choice | Alternatives | Rationale |
|----------|--------|--------------|-----------|
| Los tres casos en alcance | A + B + C | Solo A/B; diferir C | El usuario quiere el autoservicio incluido |
| Cuándo asignar el mozo | Al PEDIR (B) / al PAGAR (C) | Siempre al pagar; siempre al pedir | En B el pago es al final; en C el pago habilita la cocina |
| Barrera anti-abuso | Confirmación (B) + pagar-primero (C) | Geofencing; token rotativo | Simple, robusto, ya encaja con el flujo |
| Granularidad del aviso "listo" | A nivel ORDEN (todos los ítems `READY`) | Por ítem; por tanda | No spamear al mozo |
| Auto-asignación (C) | Round-robin entre fichados + pool fallback | Sector; pool puro | Usa el fichaje existente; sector no está mapeado |
| Config del QR | Selector de MODO con descripción en la UI | Toggles crudos | El dueño elige claro; oculta la complejidad técnica |
| Entrega del aviso | 2 fases: SSE en vivo → push real | Solo push desde el día 1 | No bloquear el valor esperando montar APNs |
| Fuente de verdad del dueño | `TableSession.waiter_id` | Campo nuevo en Order | La sesión ya es compartida QR/mozo/KDS/pago |

---

## Research Summary

**Market Context**
- El **abuso de QR self-order** (pedir sin estar en la mesa / sin pagar) es un problema conocido del rubro; las dos defensas estándar son **confirmación del mozo** (sit-down) y **pre-pago** (quick-service). Este PRD adopta ambas según el modo.
- Presentar la config como **modos con nombre** (no flags técnicos) es práctica común para que el dueño no-técnico entienda el trade-off.

**Technical Context**
- Ciclo de ítem y estado `READY` ya definidos (`domain/order/value_objects.py`); `march()` (`entities.py:126-138`) hace `PENDING→SENT`; el KDS solo muestra `SENT`/`PREPARING` (`order_repo.py:18`).
- `requires_confirmation` gatea la cocina en un único punto (`self_order.py:147`, `send=not requires_confirmation`).
- El self-pay es siempre al final e independiente (`pay_table_bill.py`); no hay pagar-primero → es feature nueva.
- La `TableSession` es compartida entre QR/mozo/KDS/pago (`use_cases.py:37-40`), y `TableSession.waiter_id` es el lugar correcto para el dueño.
- SSE de realtime disponible; push aún no.

---

*Generated: 2026-09-03*
*Status: DRAFT - needs validation*
