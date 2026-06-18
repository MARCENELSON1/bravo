# BRAVO — El cerebro del local

> SaaS multi-tenant de operaciones para PyMEs de hospitality (restaurantes primero; hoteles/turismo en fases futuras). Wedge: comandas digitales + cobro/captura de pagos + facturación AFIP + fichaje + **copiloto IA conversacional en español**.

## Problem Statement

El dueño/encargado de un restaurante PyME en Argentina pierde tiempo y plata porque sus operaciones viven en silos desconectados: comanderas de papel, WhatsApp, Excel, un sistema de facturación aparte y los cobros repartidos entre posnet, transferencias y distintas billeteras QR. No sabe con certeza cuánto vendió cada mozo, cuántas horas reales trabajó cada empleado, qué plato deja más margen, dónde se le va la mercadería, ni qué pagos entraron por cada medio — y para cada respuesta tiene que cruzar planillas a mano. El costo de no resolverlo es continuo: decisiones a ciegas sobre compras, turnos y precios, más mermas, errores de facturación y cobros sin conciliar.

## Evidence

- Investigación de mercado (`.claude/PRPs/research/mercado-hospitality-ar.md`): los líderes locales (Fudo, Maxirest, Bistrosoft) resuelven comandas/cobro/facturación pero **ninguno ofrece consulta conversacional en lenguaje natural** sobre el negocio — es el gap real en LatAm.
- AFIP/ARCA es obligatorio y complejo (WSAA + WSFEv1, comprobantes A/B/C); hoy el dueño usa un sistema separado del de operaciones, lo que fragmenta los datos.
- Cobros fragmentados: Mercado Pago, QR interoperable (Transferencias 3.0 del BCRA — un QR acepta todos los bancos/billeteras), y posnet/tarjeta (Payway/Fiserv) conviven sin un registro unificado.
- Maxirest ya comunica "alertas inteligentes" → **no nos posicionamos en alertas**; el diferenciador defendible es la **IA conversacional**.
- TAM estimado ~25k–67k establecimientos gastronómicos en Argentina (research).
- *Assumption a validar:* la disposición a pagar y la frecuencia de uso del copiloto se confirman recién con usuarios reales (ver Success Metrics).

## Proposed Solution

Una **web app responsive** (escritorio + tablet + móvil, con vistas separadas por rol) y multi-tenant, donde el restaurante opera todo el ciclo del local en un solo lugar — comandas (mozo→cocina/KDS), **captura y conciliación de pagos** (posnet, transferencias y QR), facturación AFIP nativa, fichaje de empleados, stock/food-cost y reservas — y, sobre esos datos unificados, un **copiloto IA al que se le pregunta en español** ("¿cuánto vendió Juan esta semana?", "¿qué plato me deja más margen?", "¿cuánto entró por QR vs posnet ayer?"). El backend se construye con **Clean Architecture + Ports & Adapters + SOLID + Repository + DI por contenedor** para que cada módulo y cada servicio externo (AFIP, LLM, pasarelas de pago) entre o se reemplace **sin reconstrucciones que rompan el resto**. AFIP y cada pasarela de pago viven detrás de un port (reversibles / intercambiables). Frontend Vite + React + Tailwind v4 + shadcn con design system Cult UI.

## Key Hypothesis

Creemos que **un copiloto conversacional en español que ya tiene todos los datos del local** va a **eliminar el tiempo y la plata que el dueño pierde cruzando planillas y operando a ciegas** para **dueños/encargados de restaurantes PyME en Argentina**.
Lo sabremos cuando **los locales activos le hagan ≥3 consultas útiles por semana al copiloto y declaren que reemplazó su Excel/planilla**, con adopción sostenida a 60 días.

## What We're NOT Building (v1)

- **Marketing** (fidelidad, promos, reseñas con IA) — diluye el wedge; va al roadmap.
- **CRM de clientes** — depende de tener volumen de datos de comensales que aún no existe.
- **Análisis de competencia** — feature "nice to have" que no valida la hipótesis central.
- **Vertical hoteles / turismo** — modelo de negocio y dominio distintos; fase posterior.
- **Multi-país / multi-idioma** — el wedge es AFIP nativo + español rioplatense; foco Argentina.
- **App de escritorio nativa (Electron/Tauri) y hardware dedicado (comanderas)** — se resuelve con web app responsive + BYOD; hardware nativo es evaluación futura.

> Nota: **Stock, Reservas y captura de pagos (incl. posnet) SÍ están en v1** (decisión del usuario).

## Success Metrics

| Metric | Target | How Measured |
|--------|--------|--------------|
| Uso del copiloto | ≥3 consultas útiles/semana por local activo | Telemetría de consultas + feedback 👍/👎 |
| Reemplazo de planillas | ≥60% de locales activos declaran que dejaron el Excel | Encuesta in-app a 30/60 días |
| Adopción de comandas digitales | ≥80% de comandas cargadas en digital (vs papel) | Ratio comandas/servicio en el sistema |
| Facturación AFIP exitosa | ≥99% de comprobantes con CAE OK | Tasa de éxito de emisión (WSFEv1) |
| Pagos conciliados automáticamente | ≥90% de cobros matcheados con su comanda sin intervención | Pagos conciliados / pagos totales |
| Retención de locales | ≥70% activos a 60 días | Locales con actividad / locales onboardeados |

## Open Questions

- [ ] PSP/agregador para el **QR interoperable (Transferencias 3.0)** y para la **conciliación de posnet (Payway/Fiserv)**: ¿integración directa o vía agregador?
- [ ] Detección de **transferencias** entrantes: ¿API bancaria, lectura de CVU/CBU, o conciliación por reporte?
- [ ] AFIP: orden interno de homologación de los tipos A/B/C (aunque van todos en v1).
- [ ] Copiloto: definición del **set de evals** para medir alucinación antes de exponerlo.
- [ ] Modelo de conciliación pago↔comanda↔comprobante: ¿match automático por monto+referencia con cola de excepciones?

---

## Users & Context

**Primary User**
- **Who**: Dueño/a o encargado/a de un restaurante chico-mediano en Argentina (1–3 locales, 5–30 empleados). No es técnico.
- **Current behavior**: Mezcla comanderas de papel, WhatsApp, Excel, un sistema de facturación separado y cobros repartidos entre posnet/QR/transferencias; arma reportes a mano cruzando planillas.
- **Trigger**: Cierra la caja a la noche y necesita saber cómo fue el día/semana (ventas por mozo, horas, márgenes, stock, qué entró por cada medio de pago) para decidir compras, turnos y precios.
- **Success state**: Le pregunta al copiloto en español y obtiene el dato confiable al instante, sin armar nada.

**Job to Be Done**
Cuando **termino el servicio y quiero entender cómo fue el día/semana**, quiero **preguntarle en español a un sistema que ya tiene mis datos**, para **tomar decisiones (compras, turnos, precios) sin perder tiempo armando reportes**.

**Non-Users**
- Cadenas grandes / franquicias con ERP propio.
- Hoteles y turismo (fases futuras).
- Dark kitchens 100% delivery sin salón (no hay mozos/mesas, que es el corazón inicial).
- Mercados fuera de Argentina.

**Roles (RBAC — cada uno ve solo lo suyo)**

| Rol | Qué ve | Dispositivo típico |
|-----|--------|--------------------|
| Dueño | Todo: reportes, copiloto, config, stock, reservas, pagos | PC + móvil |
| Encargado | Operación diaria, fichaje, stock, reservas | PC / tablet |
| Mozo | Tomar comandas | Celular (BYOD) |
| Cocina | KDS (comandas entrantes) | Pantalla grande / tablet |
| Caja | Cobro, captura de pagos, facturación AFIP | PC / tablet |

---

## Solution Detail

### Core Capabilities (MoSCoW)

| Priority | Capability | Rationale |
|----------|------------|-----------|
| Must | Multi-tenant (RLS + `tenant_id`) + auth/roles (RBAC) | Base no negociable; aísla datos por local |
| Must | Web app responsive (escritorio + tablet + móvil), vistas por rol | Requisito del usuario; un solo código |
| Must | Comandas digitales (mozo→cocina/KDS) | Espina dorsal: genera el dato de todo lo demás |
| Must | Captura y conciliación de pagos (posnet, transferencias, QR) vía port `PasarelaDePago` | Requisito del usuario; unifica cobros fragmentados |
| Must | Facturación AFIP A/B/C (comprobante válido) | Obligatorio y diferenciador (AFIP nativo) |
| Must | Fichaje (horas, extras, mesas/ventas por mozo) | Derivado de la comanda; dolor directo del dueño |
| Must | Stock / inventario + food cost (manual + receta opt-in, proveedores, alertas de quiebre) | Decisión del usuario: plata directa (mermas, costo) |
| Must | Reservas + no-shows (agenda, confirmaciones) | Decisión del usuario: ocupación y no-shows |
| Must | Copiloto IA conversacional (text-to-SQL con guardrails, read-only, cross-domain) | El diferenciador y la hipótesis central |
| Should | Alertas proactivas básicas | Valor extra; NO es el posicionamiento (Maxirest ya lo comunica) |
| Should | Dashboard visual clásico (gráficos) | Complementa al copiloto para quien prefiere ver |
| Could | Señas/depósitos en reservas, links de pago online | Mejora reservas y cobro, no bloquea v1 |
| Won't | Marketing, CRM, análisis de competencia, hoteles, multi-país, app nativa desktop | Diluyen el wedge / fases futuras |

### MVP Scope

Un restaurante puede, en una web app responsive y por tenant aislado: cargar la **comanda** (mozo→cocina/KDS), **cobrar capturando el pago** por posnet/transferencia/QR (Mercado Pago + QR interoperable + Payway), **facturar** con AFIP, **fichar empleados** (horas/extras + mesas y ventas por mozo derivadas de la comanda), gestionar **stock/food-cost** y **reservas/no-shows**, y **preguntarle al copiloto** en lenguaje natural sobre todo eso, con respuestas read-only, scoped por tenant y con la fuente del dato a la vista.

### User Flow (camino crítico al valor)

1. El mozo abre una mesa y carga la **comanda** desde su celular → la cocina la ve en el **KDS**.
2. Al cerrar la mesa, la **caja cobra** (QR / posnet / transferencia) → la transacción se **captura y concilia** contra la comanda, y se **emite el comprobante AFIP** (CAE).
3. La venta y las mesas atendidas quedan **atribuidas al mozo**; las horas se registran en **fichaje**; los insumos descuentan **stock**.
4. A la noche, el dueño abre el **copiloto** y pregunta en español → obtiene el dato con su fuente.

---

## Technical Approach

**Feasibility**: MEDIUM — el stack y los patrones son conocidos; el riesgo se concentra en **AFIP** (regulado, homologación, A/B/C juntos), la **conciliación de posnet/tarjeta presente** (no es tiempo real) y la **no-alucinación del copiloto** (text-to-SQL).

**Architecture Notes** (guía completa y vinculante: `docs/architecture/backend-clean-architecture.md`)
- Backend **FastAPI** con **Clean Architecture + Ports & Adapters + SOLID + Repository + DI por contenedor (`dependency-injector`)**. Regla de oro: `presentation → application → domain ← infrastructure`.
- `domain` es Python puro (sin FastAPI/SQLAlchemy/anthropic/SDKs de pago). Casos de uso dependen de **ports**, no de implementaciones.
- **Multi-tenant**: toda query filtra por `tenant_id` + **RLS en Postgres** como red de seguridad. Credenciales de cada proveedor (AFIP, pasarelas) son **config por tenant**, con secretos aislados.
- **Pagos**: port `PasarelaDePago` con un adapter por proveedor (`MercadoPagoAdapter`, `QrInteroperableAdapter` / Transferencias 3.0, `PaywayAdapter` / posnet). Entidad de dominio `Pago`/`Transaccion` **neutral** (mappers a cada proveedor). Dos modos de captura: **webhooks en tiempo real** (MP, QR interoperable) y **conciliación batch** (posnet/tarjeta vía reportes del adquirente, transferencias vía CVU/CBU). Conciliación final pago↔comanda↔comprobante.
- **AFIP**: port `FacturacionElectronica`, adapter propio (WSAA + WSFEv1), tipos A/B/C. Build reversible a Buy.
- **Copiloto**: port `CopilotoLLM` (adapter Anthropic). **text-to-SQL con guardrails obligatorios**: rol de DB read-only dedicado, inyección forzada de `tenant_id`, schema acotado (allowlist de vistas/tablas), `LIMIT`+timeout, validación del SQL (sin DDL/DML), mostrar SQL+fuente al usuario, suite de evals de alucinación.
- Frontend: **web app responsive** (un solo código, layouts por dispositivo) en capas — UI (Cult UI vía shadcn MCP) / estado / **datos (clientes de API inyectables, no `fetch` suelto)** — con **RBAC** por rol.

**Technical Risks**

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| AFIP: A/B/C juntos + WSAA/WSFEv1 + homologación | H | Aislar tras port `FacturacionElectronica`; orden interno de homologación; reversible a Buy |
| Posnet/tarjeta: conciliación (no tiempo real) | H | Modelo de conciliación batch + cola de excepciones; arrancar por rieles webhook (MP, QR) y sumar posnet con margen |
| Copiloto alucina números (text-to-SQL) | M/H | Read-only, `tenant_id` forzado, schema acotado, validación de SQL, mostrar fuente, evals |
| Fuga de datos entre tenants | M | Filtro `tenant_id` obligatorio + RLS + tests de aislamiento |
| Scope grande de v1 (stock+reservas+pagos completos) | H | Secuenciar por fases dentro de v1; arquitectura modular para entrega escalonada |
| Incumbentes copian el copiloto (12–24 meses) | M | Velocidad + profundidad de datos + UX conversacional como foso |

---

## Implementation Phases

<!--
  STATUS: pending | in-progress | complete
  PARALLEL: phases que pueden correr en simultáneo
  DEPENDS: phases que deben completarse antes
  PRP: link al plan generado cuando exista
-->

| # | Phase | Description | Status | Parallel | Depends | PRP Plan |
|---|-------|-------------|--------|----------|---------|----------|
| 1 | Fundaciones | Scaffold Clean Arch + DI container, Postgres, multi-tenant (`tenant_id`+RLS), auth/roles (RBAC), config por tenant | pending | - | - | - |
| 2 | Comandas + KDS | Dominio Comanda/Mesa/Item, flujo mozo→cocina, KDS web | pending | - | 1 | - |
| 3 | Cobro + Pagos | Port `PasarelaDePago`; adapters MP, QR interoperable (T3.0), Payway/posnet; captura webhooks + conciliación batch; entidad `Pago`; match pago↔comanda | pending | with 5, 6, 7 | 2 | - |
| 4 | Facturación AFIP | Port `FacturacionElectronica`, adapter AFIP (WSAA/WSFEv1), tipos A/B/C, CAE | pending | - | 3 | - |
| 5 | Fichaje | Horas/extras + mesas y ventas por mozo derivadas de la comanda | pending | with 3 | 2 | - |
| 6 | Stock + Food cost | Insumos, proveedores, descuento por venta (receta opt-in), alertas de quiebre | pending | with 3 | 2 | - |
| 7 | Reservas | Agenda, confirmaciones, no-shows | pending | with 3 | 1 | - |
| 8 | Copiloto IA | Port `CopilotoLLM`, text-to-SQL con guardrails, cross-domain, fuentes, evals | pending | - | 2,3,4,5,6,7 | - |
| 9 | Alertas + Dashboard | Alertas proactivas + dashboard visual | pending | - | 8 | - |

### Phase Details

**Phase 1: Fundaciones**
- **Goal**: Esqueleto del backend con Clean Arch listo para agregar módulos sin fricción.
- **Scope**: Estructura `backend/app/{domain,application,infrastructure,presentation}`, `container.py`, `config.py`, Postgres + Alembic, multi-tenant (`ContextVar` + `tenant_id` + RLS), auth/roles (RBAC), config por tenant.
- **Success signal**: Endpoint aislado por tenant, DI cableada, test de override con fake, RLS verificada.

**Phase 2: Comandas + KDS**
- **Goal**: Capturar la comanda digital y mostrarla en cocina.
- **Scope**: Entidades `Comanda`/`Mesa`/`ItemComanda`, casos de uso de alta/modificación, KDS web.
- **Success signal**: Un mozo crea una comanda y la cocina la ve en (cuasi) tiempo real.

**Phase 3: Cobro + Pagos**
- **Goal**: Capturar y conciliar los cobros por todos los rieles.
- **Scope**: Port `PasarelaDePago`, adapters `MercadoPago` + `QrInteroperable` (T3.0) + `Payway` (posnet); entidad de dominio `Pago`; captura por webhooks (MP, QR) y conciliación batch (posnet, transferencias); match pago↔comanda; cola de excepciones.
- **Success signal**: Un cobro por QR y uno por posnet quedan registrados y conciliados con su comanda.

**Phase 4: Facturación AFIP**
- **Goal**: Emitir comprobante válido sobre el cobro.
- **Scope**: Caso de uso `CerrarYFacturar`, port `FacturacionElectronica`, adapter AFIP (WSAA + WSFEv1), tipos A/B/C, CAE, manejo de errores.
- **Success signal**: Comprobantes A, B y C con CAE emitidos en homologación.

**Phase 5: Fichaje**
- **Goal**: Registrar horas/extras y atribuir mesas/ventas por mozo.
- **Scope**: Fichaje (entrada/salida), cálculo de extras, derivación de mesas/ventas desde la comanda.
- **Success signal**: Reporte por mozo: horas, extras, mesas atendidas, ventas.

**Phase 6: Stock + Food cost**
- **Goal**: Controlar inventario y costo de mercadería.
- **Scope**: Insumos, proveedores, descuento de stock por venta (receta/ficha técnica opt-in), alertas de quiebre.
- **Success signal**: Vender un plato con receta cargada descuenta sus insumos y dispara alerta al mínimo; sin receta, ajuste manual.

**Phase 7: Reservas**
- **Goal**: Gestionar reservas y no-shows.
- **Scope**: Agenda por mesa/turno, confirmaciones, marca de no-show.
- **Success signal**: Reserva creada, confirmada y marcada como no-show, visible en el servicio.

**Phase 8: Copiloto IA**
- **Goal**: Responder en español preguntas sobre todo el negocio, sin alucinar.
- **Scope**: Port `CopilotoLLM` (adapter Anthropic), text-to-SQL con guardrails (read-only, `tenant_id` forzado, schema acotado, validación, fuente), evals.
- **Success signal**: Preguntas cross-domain ("ventas por mozo", "food cost de la semana", "QR vs posnet de ayer", "no-shows del finde") correctas y con fuente.

**Phase 9: Alertas + Dashboard**
- **Goal**: Empujar insights y permitir vista visual.
- **Scope**: Alertas proactivas básicas + dashboard de gráficos.
- **Success signal**: Alerta accionable disparada y dashboard con métricas clave.

### Parallelism Notes

- **3, 5, 6 y 7** corren en paralelo tras Comandas (P2): Pagos, Fichaje y Stock dependen de la comanda; Reservas solo de Fundaciones.
- **4 (AFIP)** depende de Cobro (P3): se factura sobre el cobro capturado.
- **8 (Copiloto)** se puede andamiar temprano (port + adapter), pero su valor real aparece con los datos de P2–P7 → depende de ellas.
- **9** depende del copiloto (P8).

---

## Decisions Log

| Decision | Choice | Alternatives | Rationale |
|----------|--------|--------------|-----------|
| Backend | FastAPI (Python) | NestJS, .NET, Go+Gin, Java/Spring | Velocidad, ecosistema IA, fit con copiloto; requiere `dependency-injector` + disciplina |
| Arquitectura | Clean Arch + Ports&Adapters + SOLID + Repository + DI | MVC simple, capas laxas | Cambios sin reconstrucciones que rompan; swaps reversibles |
| Contenedor DI | `dependency-injector` | Solo `Depends` de FastAPI | IoC real, override con fakes en tests |
| Multi-tenant | RLS + `tenant_id` | Schema-per-tenant | Simple de operar/migrar, escala a miles de locales chicos |
| AFIP | Build, tipos A/B/C juntos | Buy; C primero / A-B primero | Cobertura total desde el lanzamiento (usuario); concentra riesgo, reversible a Buy vía port |
| Captura de pagos | Port `PasarelaDePago`: MP + QR interoperable (T3.0) + Payway/posnet, todos en v1 | Solo MP; sin posnet | Cobertura total de cobros (usuario); posnet es el riel más complejo (conciliación) |
| Copiloto | text-to-SQL con guardrails | Tool-calling acotado / híbrido | Máxima flexibilidad (usuario); exige blindaje fuerte para no alucinar |
| Stock | Manual + receta opt-in | Receta obligatoria / solo manual | Baja fricción de adopción, valor creciente |
| Dispositivos / cliente | Web app responsive (escritorio+tablet+móvil) + RBAC, BYOD | App nativa desktop (Electron/Tauri) / hardware dedicado | Un solo código, cero hardware que comprar |
| Posicionamiento | IA conversacional | Alertas proactivas | Maxirest ya comunica alertas; lo conversacional es el gap |
| Frontend design system | Cult UI vía shadcn MCP | Componentes a mano | Velocidad y consistencia visual |
| Idioma del dominio | Español (ubiquitous language) | Inglés | Dominio rioplatense; plomería técnica en inglés |

---

## Research Summary

**Market Context** (`.claude/PRPs/research/mercado-hospitality-ar.md`)
- Competidores (Fudo, Maxirest, Bistrosoft, Loyverse, Toast, Square) cubren comandas/cobro/facturación; **ninguno** ofrece consulta conversacional NL → gap real.
- Maxirest comunica "alertas inteligentes" → no posicionarse en alertas.
- AFIP/ARCA: WSAA + WSFEv1, comprobantes A/B/C/M; complejidad y homologación.
- TAM ~25k–67k establecimientos en Argentina.

**Payments Context (Argentina)**
- **Mercado Pago**: Orders API para QR (estático/dinámico/híbrido), tarjetas y wallet, con **webhooks** en tiempo real ([docs](https://www.mercadopago.com.ar/developers/es/reference)).
- **QR interoperable / Transferencias 3.0 (BCRA)**: por norma, **un QR acepta cualquier banco/billetera** (Santander, BBVA, MODO, etc.) → una sola integración cubre a todos ([BCRA](https://www.bcra.gob.ar/en/transfers-3-0/)).
- **MODO**: wallet de 30+ bancos; se integra vía Payway/Clover/Posnet ([comercios](https://www.modo.com.ar/comercios)).
- **Posnet / tarjeta presente (Payway, ex-Prisma)**: el riel más complejo; captura por **conciliación de reportes del adquirente**, no por webhook en vivo.

**Technical Context** (`docs/architecture/backend-clean-architecture.md`)
- Ports & Adapters hace AFIP, pasarelas de pago y LLM reversibles/intercambiables con un cambio en `container.py`.
- Multi-tenant por `tenant_id` + RLS; copiloto text-to-SQL read-only scoped por tenant con guardrails.
- Frontend en capas con clientes de API inyectables, web app responsive + RBAC.

---

*Generated: 2026-06-18*
*Status: DRAFT - needs validation*
