# NÚCLEO — El sistema operativo y el cerebro del local

> **Codename provisorio (NÚCLEO).** Nombre comercial a definir (distinto de "BRAVO" y "Ratiot").
> **Supersede** a `.claude/PRPs/prds/bravo-cerebro-del-local.prd.md` (que queda como referencia histórica).
> SaaS **multi-tenant** para PyMEs de hospitality en Argentina (restaurantes primero, hoteles como rubro habilitado). **Una sola plataforma, dos capas:** captura (motor operativo) → inteligencia (asesor financiero + copiloto).

## Problem Statement

El dueño/encargado de un restaurante u hotel PyME en Argentina pierde tiempo y plata por **dos dolores encadenados**: (1) sus operaciones viven en silos desconectados —comanderas de papel, WhatsApp, Excel, facturación aparte, cobros repartidos entre posnet/transferencias/QR— y (2) sobre ese desorden **no puede leer su propia realidad financiera**: no sabe con certeza cuánto ganó, qué plato/servicio le deja margen, cuánto se le va en comida y personal, ni qué hacer mañana. Hoy, para cada respuesta cruza planillas a mano. El costo es continuo: decisiones a ciegas sobre compras, precios y turnos, más mermas, errores de facturación y cobros sin conciliar.

## Evidence

- Investigación de mercado (`.claude/PRPs/research/mercado-hospitality-ar.md`): los líderes (Fudo, Maxirest, Bistrosoft) resuelven comandas/cobro/facturación pero **ninguno ofrece lectura financiera conversacional ni asesor proactivo en pesos** — gap real en LatAm.
- **Discovery en marcha (Villa Carlos Paz):** base de ~35 prospectos reales (mayormente hoteles + restaurantes/pubs) con seguimiento de encuestas; las preguntas de discovery confirman que el dolor más agudo y universal es **financiero/administrativo** (estacionalidad, comisiones de cobro, conciliación, capital de trabajo).
- **Activo técnico ya construido:** Fase 1 (Fundaciones + Identidad) implementada y validada — Clean Architecture + DI, multi-tenant (`tenant_id` + Postgres RLS), login completo (JWT access+refresh con cookie HttpOnly, RBAC, audit), 52 tests verdes. Frontend React 19 + Vite en capas iniciado.
- **Pensamiento de producto de la capa de inteligencia** (prototipo "Ratiot"): traducir métricas a **conclusiones en pesos con acción concreta** (food cost, labor cost, prime cost, RevPASH, punto de equilibrio, mermas), asesor proactivo, reporte para el contador, WhatsApp del lunes.
- *Assumption a validar:* disposición a pagar y frecuencia de uso se confirman con los pilotos (ver Success Metrics y Open Questions).

## Proposed Solution

Una **plataforma web responsive, multi-tenant, de dos capas**:

1. **Capa de Captura — Motor operativo (system of record).** El local opera todo el ciclo adentro: comandas (mozo→cocina/KDS), cobro y conciliación de pagos (MercadoPago, QR interoperable T3.0, posnet/Payway), **facturación AFIP nativa**, fichaje, stock/food-cost y reservas. **Se construye PRIMERO**: genera dato first-party limpio y categorizado, y es el moat profundo difícil de copiar.

2. **Capa de Inteligencia — Asesor financiero + copiloto.** Sobre ese dato nativo se monta el **asesor que habla en pesos** (no en % sueltos): KPIs traducidos a conclusiones y una sola acción concreta, insights proactivos ("trabaja mientras el dueño duerme"), **reporte para el contador** (Excel + IVA discriminado), reporte del lunes por WhatsApp, **copiloto conversacional** (preguntas en lenguaje natural, text-to-SQL con guardrails) y CRM rubro-aware. Se construye **DESPUÉS**, alimentándose del modelo canónico.

El backend mantiene **Clean Architecture + Ports & Adapters + SOLID + Repository + DI por contenedor**, de modo que cada servicio externo (AFIP, pasarelas de pago, LLM) vive detrás de un port (reversible/intercambiable). La capa de inteligencia consume un **modelo canónico** vía read models (CQRS-lite: tablas operativas → proyecciones/vistas materializadas en el mismo Postgres multi-tenant, con **RLS también en la capa analítica** porque son datos de plata). **Rubro-aware** (restaurante/hotel) en el onboarding, priorizando **restaurante** para el MVP.

## Key Hypothesis

Creemos que **capturar la operación en la fuente y, sobre ese dato limpio, darle al dueño un asesor financiero en pesos + un copiloto en español** va a **eliminar el tiempo y la plata que pierde operando a ciegas y cruzando planillas**, para **dueños/encargados de restaurantes (y luego hoteles) PyME en Argentina**.
Lo sabremos cuando **los locales activos operen el día a día en NÚCLEO, declaren que reemplazó su Excel/planilla, y paguen una suscripción mensual sostenida a 60 días** (con ≥3 consultas útiles/semana al asesor/copiloto cuando esa capa esté viva).

## What We're NOT Building (v1)

- **Marketing** (fidelidad, promos, reseñas con IA) — diluye el wedge; roadmap posterior.
- **CRM genérico de clientes** más allá del **CRM rubro-aware** acotado de la capa de inteligencia (hotel=clientes identificados/LTV; resto=patrones).
- **Análisis de competencia** — no valida la hipótesis central.
- **Multi-idioma** (ej. portugués para Brasil) — diferido; arrancamos en español rioplatense. *(Multi-país y multi-moneda SÍ son consideración de arquitectura desde el día 1 — ver Architecture Notes — con rollout empezando por Argentina/ARS.)*
- **App de escritorio nativa (Electron/Tauri) y hardware dedicado** — se resuelve con web app responsive + BYOD.
- **Capa de inteligencia antes que el motor** — decisión explícita: motor primero (ver Decisions Log).

> Nota: a diferencia de la PRD anterior, **hoteles SÍ entran como rubro habilitado** (rubro-aware), aunque el MVP prioriza restaurante.

## Success Metrics

| Metric | Target | How Measured |
|--------|--------|--------------|
| Adopción de comandas digitales | ≥80% de comandas en digital (vs papel) | Ratio comandas/servicio |
| Facturación AFIP exitosa | ≥99% de comprobantes con CAE OK | Tasa de éxito de emisión (WSFEv1) |
| Pagos conciliados automáticamente | ≥90% de cobros matcheados con su comanda sin intervención | Pagos conciliados / totales |
| Reemplazo de planillas | ≥60% de locales activos declaran que dejaron el Excel | Encuesta in-app 30/60 días |
| Uso del asesor/copiloto (cuando exista) | ≥3 consultas útiles/semana por local activo | Telemetría + feedback 👍/👎 |
| Disposición a pagar / pricing | TBD — definir techo y plan con pilotos | Encuestas de discovery + cierres de pilotos |
| Retención de locales | ≥70% activos a 60 días | Locales con actividad / onboardeados |

## Open Questions

- [ ] **Pricing y willingness-to-pay:** plan y precio mensual (lo está midiendo el discovery de VCP).
- [ ] **Pasarelas/PSP** para QR interoperable (T3.0) y conciliación de posnet (Payway/Fiserv): ¿directo o vía agregador?
- [ ] **Detección de transferencias** entrantes: ¿API bancaria, CVU/CBU, o conciliación por reporte?
- [ ] **Captura hotelera mínima** (rubro hotel): ¿reserva→folio→cobro alcanza para el MVP rubro-aware, o requiere channel manager (Booking/Despegar) desde el día 1?
- [ ] **Set de evals del copiloto** para medir alucinación antes de exponerlo.
- [ ] **Nombre comercial** del producto unificado.
- [ ] **Reparto formal de fundadores** y modelo societario.

---

## Users & Context

**Primary User — Dueño/Encargado de restaurante PyME (Argentina)**
- **Who**: dueño o encargado de un restaurante/bar PyME (rol `OWNER`/`MANAGER`), opera en el local, no es técnico ni contable.
- **Current behavior**: comandas en papel/WhatsApp, cobros repartidos, factura en un sistema aparte, controla la plata con Excel al cierre (o no la controla).
- **Trigger**: el cierre de caja a la noche ("¿me fue bien hoy?") y el fin de mes ("¿gané o perdí? ¿qué le mando al contador?").
- **Success state**: opera el ciclo (comanda→cobro→factura) en un solo lugar y, al cerrar, ve en pesos cómo le fue y qué hacer mañana.

**Secondary Users**
- **Mozo (`WAITER`)** y **Cocina (`KITCHEN`)**: cargan/ven la comanda (KDS).
- **Cajero (`CASHIER`)**: cobra y concilia.
- **Hotelero PyME** (rubro habilitado, no prioritario en MVP): reservas/folio/cobro.
- **El contador del local** (consumidor del reporte, no usuario directo del sistema).

**Job to Be Done**
Cuando **cierro el día/mes en mi local**, quiero **operar y cobrar en un solo lugar y entender en pesos cómo me fue**, para **decidir compras, precios y turnos sin operar a ciegas ni cruzar planillas**.

**Non-Users**
Cadenas grandes con ERP propio; locales que solo quieren un POS de comandas sin interés en datos financieros; mercado fuera de Argentina (sin AFIP).

---

## Solution Detail

### Core Capabilities (MoSCoW)

| Priority | Capability | Rationale |
|----------|------------|-----------|
| Must | Fundaciones + Identidad (multi-tenant, RLS, RBAC, login) | Base compartida — **ya hecha** |
| Must | Comandas + KDS (restaurante) | Núcleo del motor; primera captura vendible |
| Must | Cobro + Pagos (MP/QR/posnet) + conciliación | Cierra el ciclo operativo y el dato de ventas |
| Must | Facturación AFIP nativa (A/B/C, CAE) | Diferenciador + obligatorio + alimenta reporte contador |
| Should | Fichaje | Habilita labor cost real para el asesor |
| Should | Stock + Food cost (receta opt-in) | Habilita food cost/mermas reales |
| Should | Modelo canónico + read models (capa analítica) | Puente captura→inteligencia |
| Should | Asesor financiero + Dashboard (en pesos) | La capa de inteligencia: el "cerebro" |
| Could | Reportes + WhatsApp + para el contador | Diferenciales de venta fuertes |
| Could | Copiloto conversacional (text-to-SQL guardrails) | Moat de IA en español |
| Could | CRM rubro-aware | Fidelización (hotel) / patrones (resto) |
| Could | Reservas + No-shows | Más relevante para hotel |
| Won't (v1) | Marketing, CRM genérico, multi-país, app nativa | Diluyen el wedge / fases futuras |

### MVP Scope

**MVP motor-first (restaurante):** **Comandas + KDS + Cobro/Pagos + AFIP** — el local opera, cobra y factura legal en un solo lugar. Es el primer slice **vendible** y la fuente de dato que después alimenta al asesor. La capa de inteligencia (modelo canónico → asesor → reportes → copiloto) se construye **después**, una vez que fluye dato real de los pilotos.

### User Flow (camino crítico)

```
Mozo abre mesa → carga comanda → Cocina la ve en el KDS → se sirve →
Cajero cobra (MP/QR/posnet) → se emite comprobante AFIP (CAE) →
[el dato queda capturado: venta + ítems + medio de pago + comprobante]
        ↓ (capa de inteligencia, fase posterior)
Dueño al cierre ve en pesos cómo le fue + una acción para mañana
```

---

## Technical Approach

**Feasibility**: **HIGH** — la Fase 1 (Clean Arch + DI + multi-tenant + RLS + identidad/RBAC) ya está construida, testeada y es la base directa de todos los módulos de captura.

**Architecture Notes**
- **Dos capas sobre una plataforma:** captura (write model, tablas operativas) → **modelo canónico** (ventas/gastos/productos/clientes/medios de pago) → **read models** (KPIs) → asesor/dashboard/copiloto.
- **CQRS-lite, no warehouse:** al inicio, proyecciones/vistas materializadas en el **mismo Postgres multi-tenant**; ETL pesado / store columnar recién a escala.
- **RLS en TODA la plataforma**, incluida la capa analítica (datos financieros por tenant).
- **Ingesta con fuentes enchufables (ports & adapters):** el modelo canónico puede alimentarse de la captura nativa (primario) y, opcionalmente, de fuentes externas (MP/POS/foto-OCR) para locales que aún no operan todo en NÚCLEO.
- **Reversibilidad:** AFIP, cada pasarela de pago y el LLM viven detrás de un port (Build, intercambiable a Buy).
- **Multi-país / multi-moneda *by design*:** todo monto es un value object `Money` (**enteros en unidad mínima** + código de moneda **ISO-4217**, ej. `ARS`), **nunca float**. El tenant tiene **país + moneda**; impuestos/facturación y pasarelas de pago son **adapters por país** detrás de sus ports (`ElectronicInvoicing`, `PaymentGateway`). Arrancamos con **Argentina/ARS** (AFIP + MP/QR/posnet); sumar un país = **nuevo adapter + config**, sin tocar el dominio. El asesor habla "en la moneda local" (pesos en AR). Formato/locale por país.
- **Rubro-aware:** el onboarding (resto/hotel) define qué módulos, métricas y lenguaje se activan.
- **Convenciones:** código 100% en inglés (incl. endpoints, DB); UX en español; errores `{code EN, message ES}`. Glosario: `Order/Table/OrderItem/Invoice/Payment/PaymentGateway/Shift/Inventory/Recipe/Supplier/Reservation/Copilot`. Roles `OWNER/MANAGER/WAITER/KITCHEN/CASHIER`.

**Technical Risks**

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Alcance enorme (motor completo + inteligencia) | H | Secuenciar estricto motor-first; MVP acotado a comandas+cobro+AFIP; entregar por fases |
| AFIP (WSAA/WSFEv1) complejo | M | Adapter aislado detrás de port; homologación temprana A/B/C |
| Conciliación de pagos multi-riel | M | Empezar por MP (webhook) ; posnet/transferencias por conciliación batch + cola de excepciones |
| Tiempo real del KDS | M | Polling con TanStack Query en el MVP; SSE/WS a futuro |
| Copiloto alucinando sobre datos de plata | M | Read-only, `tenant_id` forzado, schema acotado, validación + fuente, set de evals antes de exponer |
| Motor-first retrasa time-to-value | M | Pilotos pagos desde el MVP operativo; iniciar modelo canónico apenas haya comandas+pagos (no esperar todo el motor) |
| Manejo de plata multi-moneda (redondeo/float) | M | Value object `Money` (enteros en unidad mínima + ISO-4217) desde el primer dominio con montos (Fase 2); prohibido float; moneda por tenant |

---

## Implementation Phases

<!--
  STATUS: pending | in-progress | complete
  PARALLEL: phases que pueden correr en simultáneo
  DEPENDS: phases que deben completarse antes
  Secuencia: MOTOR (captura) primero → INTELIGENCIA (asesor/copiloto) después.
-->

| # | Phase | Description | Status | Parallel | Depends | PRP Plan |
|---|-------|-------------|--------|----------|---------|----------|
| 1 | Fundaciones + Identidad | Clean Arch + DI, multi-tenant (`tenant_id`+RLS), login completo (JWT, cookie HttpOnly, RBAC, audit) + frontend de identidad | **complete** | - | - | `.claude/PRPs/plans/completed/fase-1-fundaciones.plan.md` + `frontend-identidad.plan.md` |
| 2 | Comandas + KDS | Dominio `Order`/`Table`/`OrderItem`, flujo mozo→cocina, KDS web (restaurante) | complete | - | 1 | `.claude/PRPs/plans/completed/fase-2-comandas-kds.plan.md` |
| 3 | Cobro + Pagos | Port `PaymentGateway`; adapters `Manual` + `MercadoPago` real (link/QR) + webhook firmado; `Payment` (ingresos/egresos); conciliación → comanda `PAID` | **complete** | with 5,6 | 2 | `.claude/PRPs/plans/fase-3-cobro-pagos.plan.md` |
| 4 | Facturación AFIP | Port `ElectronicInvoicing`, adapter AFIP (WSAA/WSFEv1), tipos A/B/C, CAE | pending | - | 3 | - |
| 5 | Fichaje | `Shift`, horas/extras + mesas/ventas por mozo derivadas de la comanda | pending | with 3,6 | 2 | - |
| 6 | Stock + Food cost | `Inventory`/`Recipe`/`Supplier`, descuento por venta (receta opt-in), alertas de quiebre | **complete** | with 3,5 | 2 | `.claude/PRPs/plans/completed/fase-6-stock-food-cost.plan.md` |
| 7 | Reservas + No-shows | `Reservation`, agenda por mesa/turno, confirmaciones, no-show (más relevante para hotel) | pending | with 3,5,6 | 1 | - |
| 8 | Modelo canónico + read models | Proyecciones desde la captura (ventas/gastos/productos/clientes/medios) + read models de KPIs (CQRS-lite, RLS) | pending | with 5,6,7 | 2,3 | - |
| 9 | Asesor financiero + Dashboard | KPIs en pesos (margen, punto de equilibrio, food/labor/prime cost, mermas), insights proactivos (Actuá hoy/Esta semana/Lo que viene/Bien hecho), onboarding por rubro | pending | - | 8 | - |
| 10 | Reportes + WhatsApp + Contador | Biblioteca de reportes por destinatario; reporte del lunes por WhatsApp; export para el contador (Excel + IVA discriminado) | pending | - | 9,4 | - |
| 11 | Copiloto IA | Port `CopilotLLM` (Anthropic), text-to-SQL con guardrails (read-only, tenant forzado, schema acotado, fuente), evals | pending | with 12 | 8 | - |
| 12 | CRM rubro-aware | Hotel=clientes identificados/LTV/en-riesgo/comisiones; restaurante=patrones | pending | with 11 | 8 | - |

### Phase Details

**Phase 2: Comandas + KDS** — *Goal*: capturar la comanda digital y mostrarla en cocina. *Scope*: `Order/Table/OrderItem`, alta/modificación, KDS web (polling). *Success*: un mozo crea una comanda y la cocina la ve en cuasi tiempo real. *Nota: acá se introduce el value object `Money` (enteros en unidad mínima + ISO-4217) y la config país/moneda del tenant — infra compartida del resto del motor.*

**Phase 3: Cobro + Pagos** — *Goal*: capturar y conciliar cobros por todos los rieles. *Scope*: port `PaymentGateway`, adapters MP/QR/Payway, `Payment`, webhooks (MP/QR) + conciliación batch (posnet/transferencias), match pago↔comanda, cola de excepciones. *Success*: un cobro por QR y uno por posnet quedan registrados y conciliados con su comanda.

**Phase 4: Facturación AFIP** — *Goal*: emitir comprobante válido sobre el cobro. *Scope*: `CloseAndInvoice`, port `ElectronicInvoicing`, adapter AFIP (WSAA+WSFEv1), A/B/C, CAE. *Success*: comprobantes A/B/C con CAE en homologación.

**Phase 5: Fichaje** — *Goal*: registrar horas/extras y atribuir mesas/ventas por mozo. *Scope*: `Shift` (entrada/salida), extras, derivación desde la comanda. *Success*: reporte por mozo (horas, extras, mesas, ventas).

**Phase 6: Stock + Food cost** — *Goal*: controlar inventario y costo de mercadería. *Scope*: insumos, proveedores, descuento por venta (receta opt-in), alertas de quiebre. *Success*: vender un plato con receta descuenta insumos y dispara alerta al mínimo.

**Phase 7: Reservas + No-shows** — *Goal*: gestionar reservas y no-shows. *Scope*: agenda por mesa/turno, confirmaciones, no-show. *Success*: reserva creada, confirmada y marcada como no-show, visible en el servicio.

**Phase 8: Modelo canónico + read models** — *Goal*: puente captura→inteligencia. *Scope*: proyecciones/vistas materializadas tenant-scoped (RLS) que normalizan ventas/gastos/productos/clientes/medios a un modelo canónico + read models de KPIs. *Success*: los KPIs base (ingresos, egresos, margen, ticket, medios de pago) se leen del modelo canónico para un tenant, alimentados por la captura nativa.

**Phase 9: Asesor financiero + Dashboard** — *Goal*: que el dueño lea su negocio en pesos y sepa qué hacer. *Scope*: Home (cierre inteligente), Finanzas (diagnóstico en lenguaje natural por área), KPIs (food/labor/prime cost, punto de equilibrio, mermas, RevPASH), insights proactivos en 4 secciones, onboarding por rubro. *Success*: al cierre, el dueño ve en pesos cómo le fue + una acción concreta, sin interpretar un solo %.

**Phase 10: Reportes + WhatsApp + Contador** — *Goal*: empujar valor afuera de la app. *Scope*: biblioteca de reportes por destinatario, reporte del lunes por WhatsApp, export contador (Excel + IVA discriminado, sobre datos AFIP). *Success*: llega el WhatsApp del lunes y se descarga el reporte del contador sin trabajo manual.

**Phase 11: Copiloto IA** — *Goal*: responder en español preguntas sobre el negocio sin alucinar. *Scope*: port `CopilotLLM`, text-to-SQL con guardrails (read-only, tenant forzado, schema acotado, validación, fuente), evals. *Success*: preguntas cross-domain ("ventas por mozo", "food cost de la semana", "QR vs posnet de ayer") correctas y con fuente.

**Phase 12: CRM rubro-aware** — *Goal*: fidelizar (hotel) / leer patrones (resto). *Scope*: hotel = clientes identificados, LTV, en-riesgo, comisiones de canal; restaurante = patrones de visita. *Success*: identificar un huésped en riesgo con su LTV y disparar contacto; ver patrones de días/horarios en restaurante.

### Parallelism Notes

- **Motor primero, inteligencia después** es la regla de oro. Pero la Fase 8 (modelo canónico) **depende solo de 2 y 3** (comandas + pagos), no de todo el motor: puede arrancar en paralelo con 5/6/7. Así el asesor empieza a consumir las fuentes más ricas sin esperar a stock/reservas.
- 5, 6 y 7 pueden correr en paralelo con 3 (dependen de 2 o de 1).
- 11 y 12 corren en paralelo una vez que existe el modelo canónico (8).

---

## Decisions Log

| Decision | Choice | Alternatives | Rationale |
|----------|--------|--------------|-----------|
| Secuencia/wedge | **Motor operativo primero, asesor después** | Asesor primero (time-to-value) | Decisión del usuario: construir el moat profundo + dato first-party limpio y no depender de ETL frágil de fuentes externas |
| Vertical de entrada | **Rubro-aware, priorizando restaurante** | Solo restaurante / hotel primero | Restaurante = captura más rica (comandas) y mejor alimento del asesor; hotel queda habilitado por los prospectos de VCP |
| Unificación | **Un producto, dos capas (captura + inteligencia)** | Dos productos + ETL en el medio | Las capas son complementarias; los perfiles de los fundadores calzan (tech=motor, finanzas=asesor/GTM) |
| Capa analítica | **CQRS-lite (read models en el mismo Postgres + RLS)** | Warehouse + ETL/CDC separado | Evitar over-engineering en MVP de PyME; escalar a warehouse recién con volumen |
| Arquitectura backend | **Clean Arch + Ports & Adapters + DI** (reusar Fase 1) | Reescribir | Ya construido, testeado y reversible (AFIP/pagos/LLM detrás de ports) |
| Nombre | **Codename NÚCLEO (placeholder)** | BRAVO / Ratiot | Comercial a definir; distinto de ambos |
| Alcance geográfico | **Multi-país / multi-moneda *by design*, Argentina/ARS primero** | Solo Argentina (PRD vieja) | La arquitectura de ports permite sumar país = adapter + config; no hardcodear ARS evita reescrituras a futuro |

---

## Research Summary

**Market Context**: ver `.claude/PRPs/research/mercado-hospitality-ar.md`. Los incumbentes resuelven operación pero no la **lectura financiera conversacional + asesor proactivo en pesos**; ahí está el diferenciador defendible, sumado a **AFIP nativo**. Discovery real en VCP (mayormente hoteles) confirma el dolor financiero/administrativo como el más agudo.

**Technical Context**: Fase 1 construida (Clean Arch, multi-tenant, RLS, identidad/RBAC, 52 tests). La arquitectura de ports & adapters habilita motor-first con captura reversible y una capa de inteligencia desacoplada vía modelo canónico. Frontend en capas (clientes inyectables + TanStack Query) ya iniciado.

---

*Generated: 2026-06-20*
*Status: DRAFT — needs validation (pricing, captura hotelera, nombre, reparto de fundadores)*
