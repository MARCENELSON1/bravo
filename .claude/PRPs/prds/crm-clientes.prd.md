# CRM / Clientes — Ratiot le dice al dueño a quién contactar hoy

> Fuente: `~/Downloads/pantalla-clientes-crm-spec.txt` ("PANTALLA DE CLIENTES (CRM) — ESPECIFICACIÓN", Ratiot v1). Verificado contra el código real (payments con `method`/`external_ref`, reservas con email; commit `af729e1`).

## Problem Statement

El dueño de un restaurante **no sabe quiénes son sus clientes ni cuándo dejaron de venir**. El cliente que gastaba todas las semanas se esfuma y nadie se entera hasta que pasaron meses; el que cumple años no recibe nada; el dueño no tiene forma de saber si contactar a alguien sirve. El costo es plata que se va sin pelearla: un cliente recurrente que se pierde vale mucho más que uno nuevo, y hoy no hay ningún mecanismo para detectarlo ni para actuar.

## Evidence

- **Verificado en código**: no existe entidad de cliente ni CRM; el sidebar "Clientes" apunta a `/app/reservations`. Sí existe sustrato de identidad: `payments.external_ref` (id de pagador MercadoPago), `payments.method` (CASH/CARD/TRANSFER/MERCADOPAGO/QR), y reservas con email.
- **Ventaja estructural**: como Wellnod **es el POS** (comandas propias), tenemos **todas** las órdenes → el denominador de cobertura (tickets totales) existe, cosa que la competencia no tiene.
- **Del spec**: el problema difícil no es la pantalla, es la **identidad** (el mismo tipo paga con MP hoy y tarjeta la semana que viene = dos registros); si no se resuelve, todos los números salen inflados y el dueño lo nota el primer día.

## Proposed Solution

Un CRM que **no es un listado, es una pantalla de acciones**: Ratiot identifica y segmenta solo, y le dice al dueño **a quién contactar hoy** (máx 3 acciones ordenadas por plata en juego), con un **loop de resultado** que mide si volvieron y cuánto gastaron. Todo detrás de una **regla de oro innegociable**: nunca mostrar un número inflado — cobertura siempre visible, plata en absoluto (no % del total si la cobertura es baja), mínimos estadísticos, y empty states honestos. El contacto es por **`wa.me` (deep link, sin API ni proveedor)** con opt-out. Pantalla nueva `/app/clientes` detrás de feature flag `crm_clientes_enabled` (prender de a uno).

## Key Hypothesis

Creemos que **detectar clientes en riesgo según su propio hábito y darle al dueño 3 acciones concretas por día con `wa.me`** va a **recuperar clientes que hoy se pierden en silencio**. Lo sabremos cuando la pantalla pueda mostrar, con datos reales: **"contactaste N clientes, volvieron M y gastaron $X"** — y ese X sea material.

## What We're NOT Building

- **Envío automático o masivo de WhatsApp** — v1 es solo `wa.me` con texto pre-armado; el envío por API de WhatsApp Business + consentimiento es un proyecto aparte (queda como fase futura, y sigue trabado por decisión de proveedor).
- **"Productos favoritos" / "qué pidió la última vez"** — requiere integración a nivel ítem con POS externo; nosotros lo tendríamos vía `sale_facts`, pero queda fuera de v1.
- **"Con quién venía"** — no existe en ninguna fuente de datos.
- **Matcheo por nombre** — NUNCA (genera falsos merges); solo phone/email/mp_payer_id/card_fingerprint.
- **Extrapolar/proyectar/estimar a partir de la muestra** — prohibido por la regla de oro.

## Success Metrics

| Metric | Target | How Measured |
|--------|--------|--------------|
| Loop de resultado con plata | mostrar "$X recuperados" con datos reales | `contact_log.outcome_visit_id` + gasto de la visita |
| Clientes identificados | crecer mes a mes | `count(customers identificados)` con cobertura visible |
| Acciones ejecutadas | ≥1 contacto marcado por semana por tenant activo | `contact_log` |
| Cero números inflados | 0 quejas de "esto no me cierra" | regla `can_show_share` aplicada en todos los bloques |

## Open Questions

- [ ] `card_fingerprint`: ¿tenemos BIN + últimos 4 + hash del titular desde el gateway de tarjeta? (define si el match por tarjeta entra en v1 o futuro).
- [ ] `mp_payer_id`: confirmar que `payments.external_ref` de MercadoPago contiene un id de pagador estable (no solo id de transacción).
- [ ] Recálculo: ¿incremental + on-read alcanza (analizado: sí), o se quiere el cron nocturno desde v1?
- [ ] Datos de demo: ¿se habilitan para mostrar la pantalla antes de tener volumen? (spec lo permite con bandera "Datos de ejemplo" visible).

---

## Users & Context

**Primary User**
- **Who**: Dueño/encargado (OWNER/MANAGER) de restaurante/café PyME. No hace marketing, no tiene CRM, no tiene tiempo.
- **Current behavior**: "Conoce" a algunos clientes de memoria; no tiene registro; reacciona tarde o nunca.
- **Trigger**: "Hace mucho que no viene fulano" (cuando ya es tarde), o un cumpleaños que se acuerda de casualidad.
- **Success state**: Abre la pantalla, ve 2-3 personas para contactar hoy con el mensaje listo, y a fin de mes ve cuánto recuperó.

**Job to Be Done**
Cuando **un buen cliente deja de venir sin que me dé cuenta**, quiero **que el sistema me avise a quién contactar y me arme el mensaje**, para **recuperarlo antes de perderlo del todo**.

**Non-Users**
El cliente final (no usa la pantalla), el mozo/cocina, y el dueño sin ninguna captura activa (MP/tarjeta/reserva) — para ese primero hay que activar un canal.

---

## Solution Detail

### Core Capabilities (MoSCoW)

| Priority | Capability | Rationale |
|----------|------------|-----------|
| Must | Identidad del cliente (matcheo en cascada + merge reversible) | El cimiento; sin esto todo se infla |
| Must | Regla de oro `can_show_share()` (cobertura, plata absoluta, mínimos) | Sin esto perdemos la confianza el primer día |
| Must | Motor de métricas + segmentos (Recurrentes/Nuevos/VIP/En riesgo relativo) | La materia prima de las acciones |
| Must | Acciones para hoy (máx 3) + `wa.me` + opt-out | El corazón del producto |
| Must | Loop de resultado (contactó → volvió en 30d → $) | La métrica que justifica el producto entero |
| Must | Buscador + ficha de cliente | Primera cosa usable de verdad |
| Should | Hero (frase + semáforo) + canales de captura (un bloque) | Cierra la narrativa; cosmético |
| Should | `crm_config` por restaurante (nada hardcodeado) | Un café y un resto no comparten umbrales |
| Should | `business_date` (corte 6am local) | Compartido con Productos |
| Could | Carga manual de cumpleaños / cliente | Habilita el bloque de cumpleaños |
| Won't (v1) | WhatsApp Business API (envío masivo/automático) | Consentimiento + proveedor; fase futura |
| Won't (v1) | Canales Fidelidad / WiFi con login | Requieren integraciones nuevas; fase futura |
| Won't (v1) | Match por `card_fingerprint` (si no hay dato) | Depende de datos del gateway de tarjeta |

### MVP Scope

Tickets 1→2→3→4: identidad + métricas + ficha + acciones con loop. Con eso hay valor real y la métrica que justifica todo. El hero (Ticket 5) se pule al final.

### User Flow (camino crítico)

1. Entra un pago identificable (MP/tarjeta) o una reserva → se resuelve identidad (match o cliente nuevo) → se consolida la visita → se recalculan sus métricas.
2. Dueño abre `/app/clientes` → hero + "el mes pasado contactaste 12, volvieron 5, $340.000".
3. Acciones para hoy (máx 3, por plata): "Mandale un mensaje a Juan, hace 40 días que no viene y venía cada 12. Gastó $180.000 con vos."
4. `[Ver mensaje]` → `[Contactar por WhatsApp]` (`wa.me`) → `[Marcar como contactado]` → escribe `contact_log`.
5. Si Juan vuelve dentro de 30 días → se completa `outcome_visit_id` → suma al loop del mes.

---

## Technical Approach

**Feasibility**: **MEDIUM-HIGH** — greenfield, pero con sustrato de datos parcial y patrones reutilizables.

**Architecture Notes**
- **Clean Architecture**: `domain/customer` puro (entidades Customer/Visit/Identifier/Segment), use cases sobre ports, repos en infra, RLS por `tenant_id`. Igual que el resto del backend.
- **Sustrato de identidad**: `payments.external_ref` (MP payer id), `payments.method`, reservas con email → fuentes de captura ya existentes; falta la capa de resolución/merge.
- **Proyección incremental** como `ProjectOrderSales`: cuando entra una visita → recalcula métricas del cliente. Segmentos time-based (en riesgo, VIP) se resuelven **on-read** sobre `customer_metrics` (analizado: no requiere cron para correctness).
- **Contacto**: `wa.me/<phone_e164>?text=...` con template ({nombre},{dias},{beneficio}); flag `no_contactar` respetado siempre.
- **Regla de oro** en un helper único `can_show_share(tenant, periodo)` — no replicado por componente.
- **`business_date`** como columna (corte 6am `America/Argentina/Buenos_Aires`), compartida con Productos v3.
- **Feature flag** `crm_clientes_enabled` por tenant.

**Technical Risks**

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Merge equivocado une dos personas distintas | M | Merge blando (`merged_into_id`) reversible; confianza MEDIA no auto-mergea (va a cola) |
| Números inflados por baja cobertura | H | `can_show_share`: si cobertura NULL o <60%, plata absoluta, nunca % |
| `mp_payer_id`/`card_fingerprint` no disponibles como se asume | M | Confirmar en spike; degradar a match por phone/email si falta |
| Duplicar visitas (mesa dividida, 2 tarjetas) | M | Consolidación por ventana de 3h |
| Segmentos con pocos datos | M | No mostrar segmento con <5 clientes; no percentil con <30 |

---

## Implementation Phases

| # | Phase | Description | Status | Parallel | Depends | PRP Plan |
|---|-------|-------------|--------|----------|---------|----------|
| 0 | Ruteo + flag | Ruta `/app/clientes`, reapuntar sidebar (hoy `/app/reservations`), feature flag `crm_clientes_enabled`, `business_date` (corte 6am) compartido | pending | - | - | - |
| 1 | Modelo de datos + identidad | Tablas `customers`/`customer_identifiers`/`visits`/`contact_log`/`customer_metrics` (RLS); captura desde MP/tarjeta/reserva/manual; matcheo en cascada (phone→email→mp_payer_id→card_fingerprint, nunca por nombre); merge blando reversible + cola de duplicados; consolidación de visitas (3h) | pending | - | 0 | - |
| 2 | Motor de métricas + segmentos | `customer_metrics` (gasto acumulado/30d/90d/12m, visitas, ticket, intervalo mediano ≥3 visitas, días sin venir); segmentos Recurrentes/Nuevos/VIP(percentil, ≥30)/En riesgo (relativo al hábito); `crm_config` por restaurante; regla `can_show_share()` | pending | - | 1 | - |
| 3 | Buscador + ficha | Buscador único (nombre/tel/email) + filtros (segmento/período/canal) que también filtran la lista; ficha (identificación, métricas, historial de visitas, notas autosave, duplicados pendientes, acciones) | pending | with 4 | 2 | - |
| 4 | Acciones + loop de resultado | Máx 3 acciones (riesgo/cumpleaños/cliente del mes) por plata; botón contactar `wa.me` + template + opt-out; **loop**: `[Marcar como contactado]`→`contact_log`, visita en 30d→`outcome_visit_id`, "contactaste N, volvieron M, $X" | pending | with 3 | 2 | - |
| 5 | Hero + canales de captura | Hero (una frase + semáforo + resultado del loop del mes); bloque único de canales (activados + no activados con "Te ayudamos a activarlo") | pending | - | 3, 4 | - |
| 6 | Cumpleaños + carga manual | Carga manual de cliente/cumpleaños (habilita bloque de cumpleaños que hoy no se muestra sin datos) | pending | - | 4 | - |
| 7 | WhatsApp Business API (futuro) | Envío programado/masivo con consentimiento + proveedor (trabado por decisión de proveedor; ver Fase 10 del roadmap NÚCLEO) | pending | - | 4 | - |
| 8 | Canales Fidelidad + WiFi (futuro) | Programa de fidelidad (captura de efectivo + cumpleaños) y WiFi con login como canales de identificación | pending | - | 1 | - |
| 9 | Match por tarjeta (futuro) | `card_fingerprint` (BIN + últimos 4 + hash titular), confianza MEDIA → cola de duplicados, si el gateway expone el dato | pending | - | 1 | - |

### Phase Details

**Phase 0 — Ruteo + flag**
- **Goal**: Andamiaje para prender de a uno.
- **Scope**: Ruta nueva, reapuntar sidebar, feature flag por tenant, `business_date` (columna, corte 6am). Reservas queda como pantalla aparte.
- **Success signal**: `/app/clientes` accesible solo con flag on; `business_date` calculado y guardado.

**Phase 1 — Modelo de datos + identidad** (el cimiento)
- **Goal**: Resolver que el mismo tipo con MP y tarjeta sea un solo cliente.
- **Scope**: Las 5 tablas con RLS; captura idempotente por webhook (`external_id` único por channel); cascada de matcheo (ALTA auto-mergea: phone/email/mp_payer_id; MEDIA a cola: card; nombre NUNCA); merge blando `merged_into_id` reversible; consolidación de 2 pagos en 3h = 1 visita.
- **Success signal**: Dos pagos del mismo cliente por canales distintos → un cliente, una visita.

**Phase 2 — Motor de métricas + segmentos**
- **Goal**: Segmentar solo, relativo al hábito de cada cliente.
- **Scope**: `customer_metrics` (incremental + recalc del cliente afectado); intervalo mediano solo con ≥3 visitas; "en riesgo" = intervalo≠NULL Y días_sin_venir > 2.5×intervalo Y <365; VIP percentil 90 con ≥30 clientes; `crm_config` (todos los umbrales, defaults globales); `can_show_share()`.
- **Success signal**: "En riesgo" detecta al de cada-semana a los 21 días y al de cada-90 recién a los ~225; no se muestra segmento con <5.

**Phase 3 — Buscador + ficha**
- **Goal**: Primera cosa usable de verdad.
- **Scope**: Un solo componente de lista+buscador+filtros (los chips de segmento filtran esta misma lista); ficha con identificación/métricas/historial/notas autosave/duplicados/acciones; paginado obligatorio.
- **Success signal**: Buscar por teléfono trae la ficha con historial y notas.

**Phase 4 — Acciones + loop de resultado** (el corazón)
- **Goal**: Decirle a quién contactar hoy y medir si sirvió.
- **Scope**: Máx 3 acciones por plata (riesgo / cumpleaños solo si hay ≥1 cargado / cliente del mes); `wa.me` con template + `no_contactar`; `contact_log` + matcheo de outcome en 30d + frase de resultado arriba de todo. **Si hay que recortar algo, que no sea el loop.**
- **Success signal**: "El mes pasado contactaste 12, volvieron 5, gastaron $340.000" con datos reales.

**Phase 5 — Hero + canales**
- **Goal**: Cerrar la narrativa.
- **Scope**: Hero (una frase con semáforo + resultado del loop); canales en un bloque (activados con conteo + no activados con CTA cualitativo, sin prometer "+30%").
- **Success signal**: "Identificaste 89 clientes este mes, 18% más" + el resultado del loop.

**Phase 6 — Cumpleaños + carga manual**
- **Goal**: Habilitar cumpleaños (MP/tarjeta no dan fecha de nacimiento).
- **Scope**: Carga manual de cliente/cumpleaños; el bloque de cumpleaños se muestra solo cuando hay datos.
- **Success signal**: Un cumpleaños cargado a mano aparece en las acciones de la semana.

**Phases 7–9 — Futuro** (dejadas armadas)
- **7 WhatsApp Business API**: envío programado/masivo + consentimiento + proveedor. Trabado por decisión de proveedor (converge con Fase 10 del roadmap NÚCLEO).
- **8 Fidelidad + WiFi**: nuevos canales de captura (clave para ver a los que pagan en efectivo).
- **9 Match por tarjeta**: `card_fingerprint` si el gateway expone BIN+últimos4+hash titular.

### Parallelism Notes

Fases 3 y 4 pueden ir en paralelo (ambas dependen de 2). 0→1→2 es la cadena crítica. 7/8/9 son "futuro" independientes, se activan por decisión de producto o disponibilidad de datos.

---

## Decisions Log

| Decision | Choice | Alternatives | Rationale |
|----------|--------|--------------|-----------|
| Match por nombre | NUNCA | Fuzzy por nombre | Genera falsos merges que el dueño nota |
| Merge de confianza MEDIA | A cola manual | Auto-merge | Un merge equivocado no se recupera |
| "En riesgo" | Relativo al hábito (2.5× intervalo) | Umbral fijo 60 días | El de cada-90 no está en riesgo a los 60 |
| LTV | "Gastó $X en total" (histórico) | "LTV" proyectado | No estamos proyectando; el dueño entiende mejor |
| % de facturación | Solo si cobertura ≥60% | Mostrar siempre | Con 30% de mesas identificadas, el % está inflado ~3× |
| Contacto | `wa.me` deep link | WhatsApp Business API | Sin proveedor ni consentimiento en v1; desbloquea ya |
| VIP | Percentil 90 (≥30 clientes) | Monto fijo | Un café y un resto no comparten umbral |

---

## Research Summary

**Market Context**: El CRM como "pantalla de acciones" (no listado) con loop de resultado es el diferencial: la competencia muestra listas; nadie mide "volvieron M y gastaron $X". La identidad multi-canal es el foso técnico.

**Technical Context**: Greenfield en dominio, pero con sustrato (`payments.external_ref`/`method`, reservas) y patrones reutilizables (proyección incremental, RLS, Clean Architecture, LLM Fase 9 para templates). `wa.me` desbloquea el contacto sin proveedor. Ventaja única: al ser el POS, tenemos el denominador de cobertura.

---

*Generated: 2026-08-04*
*Status: DRAFT — cubre todos los tickets del spec, con envío WhatsApp/fidelidad/tarjeta como fases futuras 7–9*
