# App Mobile nativa (Flutter) — "Wellnod en la mano"

> Generado con el flujo `/prp-prd` (ecc). Estado: **DRAFT — needs validation**.
> Relacionado: [[plan-desktop-electron]] (desktop = React/Electron), [[plan-i18n-app]], [[carta-qr-autopedido]] (comensal = web/PWA).

## Problem Statement

El personal del local (mozo, cocina, cajero, dueño) opera **de pie y con red inestable**, pero el cliente actual de Wellnod es **web**, pensada para escritorio/mostrador: lenta en mobile, pelea con el teclado del browser, **se corta si se cae la luz o el internet** (se pierde la comanda), no imprime a la comandera desde el dispositivo ni escanea el QR de mesa. El costo de no resolverlo: la operación de piso —lo más frecuente y crítico— sucede en la peor superficie posible, frenando la adopción real del producto.

## Evidence

- El backend ya es maduro y multi-tenant (Fases 1–14 + Carta QR completas en `main`); el cuello de botella dejó de ser el cerebro y pasó a **el cliente en el piso**.
- Observación del dueño (esta sesión): quiere que el equipo opere desde el celular, que **siga funcionando ante un corte de luz/internet** y sincronice al volver, y que la app tenga **todas las secciones del web menos la carta del comensal**.
- Prioridades explícitas del dueño: **fidelidad de identidad visual** innegociable + **eficiencia en dispositivo** (gama baja, toda la jornada). La curva de aprendizaje se declaró no-criterio.
- Assumption (a validar con uso real): la app nativa sube la adopción y baja las comandas perdidas vs la web mobile — se mide en piloto (ver Success Metrics).

## Proposed Solution

Una **app mobile nativa en Flutter**, cliente fino de la API FastAPI existente, para **el equipo y el dueño del local** — con **paridad de secciones respecto del web, excepto la carta del comensal** (que sigue siendo web/PWA por diseño: "escaneás y listo, sin instalar"). Se elige Flutter sobre React Native y nativo (Swift+Kotlin) porque renderiza cada pixel él mismo (Skia/Impeller → **fidelidad visual pixel-perfect e idéntica en iOS/Android**) y compila AOT a nativo sin puente JS (**eficiencia pareja en gama baja**), los dos criterios que el dueño priorizó. La pérdida de reuso de React no pesa: la UI se reescribe igual en RN, la **lógica de negocio ya vive en el backend** (cliente fino), el **cliente Dart se genera del OpenAPI** y los **design tokens se portan una vez** a un `ThemeData`. Arranca por el **piso (comanda del mozo) con modo contingencia offline desde el día 1** y se expande hasta cubrir todas las secciones.

## Key Hypothesis

Creemos que **una app nativa Flutter con captura rápida + modo contingencia offline + impresión local** va a **hacer que el equipo opere el local desde el teléfono sin miedo a cortes de red**, para el **personal y el dueño**.
Sabremos que acertamos cuando **el % de comandas/cobros hechos desde la app supere al del web, con 0 comandas/cobros perdidos ante cortes, y captura más rápida que la web mobile** (ver Success Metrics — las tres cuentan).

## What We're NOT Building

- **Carta del comensal nativa** — sigue web/PWA por diseño (sin instalación; el comensal nunca instala nada). Es el diferencial de fricción cero.
- **Lógica de negocio en el cliente** — todo el cálculo (cuenta, food cost, finanzas, AFIP, split, propinas) sigue en el backend detrás de sus ports. El cliente pide y muestra.
- **Reemplazo de la web o del desktop Electron** — la app mobile es **aditiva**, mismo backend, misma verdad.
- **Facturación AFIP con lógica propia en el dispositivo** — se orquesta contra el backend; offline se **encola** y emite al reconectar.

## Success Metrics

> El dueño eligió "todas" — las tres son objetivo del v1.

| Métrica | Target | Cómo se mide |
|---|---|---|
| Adopción (norte) | % de comandas/cobros desde la app > que desde el web, por local | Conteo por origen (`source`) en el backend, por tenant |
| Resiliencia offline | **0** comandas/cobros perdidos ante corte de luz/internet | Auditoría de la cola local vs lo sincronizado; reconciliación post-corte |
| Velocidad de captura | "abrir app → comanda enviada" por debajo de umbral (baseline web mobile) | Instrumentación cliente (tiempo de flujo) vs medición en web |
| Fidelidad visual | Paridad 1:1 con el design system, claro/oscuro, iOS+Android | Revisión visual como gate de cada fase |

## Open Questions

- [ ] **Auth móvil sin cookie** (riesgo #1): confirmar refresh/access en secure storage + renovación por header contra el backend split-domain — spike en Fase 0.
- [ ] **IA de "todas las secciones" en el teléfono**: cómo agrupar el long-tail (Productos/Finanzas/Reportes/Comprobantes/Insumos/Integraciones/CRM/Ajustes/Plataforma) bajo bottom-nav-por-rol + "Más" sin romper UX. Diseño explícito en Fase 6.
- [ ] **Pantallas pesadas con paridad completa**: ¿hasta dónde llega el editable en teléfono vs tablet? (mecanismo elegido: layouts adaptativos; validar por pantalla).
- [ ] **Panel de Plataforma** (super-admin `platform_admin`): ¿entra en la app mobile o queda solo web? (uso no-diario; candidato a diferir).
- [ ] **i18n**: idioma por dispositivo/toggle (como hoy) vs fijado por `tenant.locale` (decisión compartida con la web, aún abierta).
- [ ] **Fierros a confirmar en Fase 0** (defaults propuestos, ver Decisions Log): estado = Riverpod; codegen = openapi-generator/dio o swagger_parser; DB local = drift.

---

## Users & Context

**Primary User** — el **equipo del local**, por rol (el RBAC ya existe en el backend: `OWNER/MANAGER/WAITER/KITCHEN/CASHIER`):

- **Quién**: personal en movimiento (mozo con el celular en mano, cocina frente a tablet, cajero cerrando turno) + dueño/encargado que quiere ver la ganancia del día y preguntarle al copiloto.
- **Comportamiento actual**: operan desde la web (pensada para escritorio) o a mano; ante un corte, se frena todo.
- **Trigger**: cada mesa nueva, cada plato, cada cobro, cada cierre de turno — y cada caída de red.
- **Success state**: tomar/cobrar sin fricción desde el teléfono, sin perder nada ante un corte, con la misma identidad visual del producto.

**Job to Be Done**
Cuando **se cae la luz o el internet en pleno servicio**, quiero **seguir tomando comandas y cobrando desde el teléfono**, para **no frenar el local y que todo se sincronice solo cuando vuelva la conexión**.

**Non-Users**
El **comensal** — no instala nada; usa la Carta QR web/PWA. La app nativa es exclusivamente para el lado staff/dueño.

---

## Solution Detail

### Core Capabilities (MoSCoW)

| Prioridad | Capacidad | Rationale |
|---|---|---|
| Must | Piso + Comanda (mozo): plano de salón, tomar/editar/anular, mover/unir mesas, enviar a cocina | El corazón operativo, mayor uso diario, mayor payoff nativo |
| Must | **Modo contingencia offline** (cola local + sync al reconectar) | La promesa central: seguir operando ante corte de luz/internet |
| Must | **Impresión ESC/POS por Bluetooth** | Plan B de cocina: la comanda llega físicamente aunque el sistema esté caído |
| Must | Auth móvil (secure storage + renovación) + navegación por rol | Base sin la cual no hay app; riesgo técnico #1 |
| Must | KDS (cocina) y Caja (cobro/split/propina/arqueo) | Cierran el ciclo operativo del local |
| Should | Home + Copiloto/Asesor (LLM) | El dueño ve valor; reusa infra ya construida |
| Should | Propinas por mozo/liquidación + Fichaje (TimeClock) + Push | Completan la operación del equipo |
| Could | **Pantallas pesadas con paridad completa** (Productos v2/v3, Finanzas, Reportes, Comprobantes/AFIP, Insumos, Integraciones, CRM, Ajustes) | Paridad total con el web; con layouts adaptativos para no romper UX |
| Could | Panel de Plataforma (super-admin) | Uso no-diario; candidato a quedar solo en web |
| Won't (v1) | Carta del comensal nativa | Sigue web/PWA por diseño (fricción cero) |

### MVP Scope

**Fase 0 (fundaciones) + Fase 1 (Piso + Comanda con modo contingencia)** sobre **iOS + Android**, distribuida por **stores públicas**. Es el mínimo que valida la hipótesis: el mozo toma comandas desde el teléfono, la app imprime a la comandera por Bluetooth, y ante un corte sigue operando y sincroniza al volver.

### User Flow (camino crítico)

Login (por rol) → **bottom nav por rol** (mozo: Piso · Comanda · Caja · Más) → abrir mesa (o escanear QR con la cámara) → armar comanda (grilla de productos + modificadores + carrito) → enviar → **si hay red**: va al backend/KDS; **si no hay red**: se encola local + **se imprime el ticket a cocina por Bluetooth** → al volver la conexión, **sync automático** (backend idempotente, sin duplicar).

---

## Technical Approach

**Feasibility**: **HIGH** — el backend ya expone todo lo necesario; el trabajo es de cliente.

**Architecture Notes**
- **Cliente fino en capas** (coherente con la Clean Architecture del back): `data/` (cliente API generado + secure storage + DB local drift + colas), `domain/` fino (modelos de vista), `state/` (Riverpod), `ui/` (widgets + `ThemeData`). Clientes de API **inyectables** (no `http` suelto en widgets), como en el front web.
- **Proyecto aditivo en `mobile/`** del monorepo — no toca `frontend/` ni `backend/` (mismo patrón que Electron fue aditivo a `frontend/`).
- **OpenAPI → cliente Dart** por codegen en CI (DTOs siempre en sync con el backend, sin escribir a mano).
- **Identidad visual**: design tokens del shell glass (claro/oscuro) portados a un `ThemeData` central; componentes de marca recreados como widgets Flutter 1:1 (sin vistas nativas por defecto → cero deriva iOS/Android).
- **Modo contingencia**: cola local (drift/SQLite) con **reintento idempotente** apoyado en la `idempotency_key` que el backend ya tiene; indicador de estado de sync; impresión ESC/POS (BLE) como salida de cocina sin red.
- **Auth móvil**: sin cookies de browser → refresh/access en **Keychain/Keystore** + renovación por header (el backend ya soporta split-domain; mismo problema/solución que el plan Electron).
- **Pantallas pesadas**: paridad completa como objetivo, con **layouts adaptativos** — teléfono usa divulgación progresiva / flujos en pasos; tablet habilita el layout denso completo.
- **Push**: FCM/APNs + endpoint de registro de device tokens; disparadores: plato listo (KDS→mozo), mesa pide la cuenta, alerta del día.

**Technical Risks**

| Riesgo | Prob. | Mitigación |
|---|---|---|
| Auth móvil sin cookie (refresh/renovación) | M | Spike en Fase 0; backend ya soporta split-domain |
| Sync con conflictos tras corte | M | Idempotencia ya existente + cola con clave + reconciliación |
| Fidelidad del port de tokens | M | `ThemeData` central + revisión visual como gate por fase |
| Variedad de impresoras ESC/POS | M | Detrás de un adapter; probar modelos reales temprano en F1 |
| "Todas las secciones" apretadas en teléfono | M | Bottom-nav-por-rol + "Más" + layouts adaptativos; IA explícita en F6 |
| Doble mantenimiento (web + mobile) | M | Acotado: no se duplica lógica (backend fino); solo se mantiene UI |
| Review de stores (Apple/Google) | L | Planificar provisioning/review temprano |

---

## Implementation Phases

<!--
  STATUS: pending | in-progress | complete
  PARALLEL: fases que pueden correr en paralelo
  DEPENDS: fases que deben completarse antes
  PRP: link al plan generado (una vez creado con /prp-plan)
-->

| # | Fase | Descripción | Status | Parallel | Depends | PRP Plan |
|---|------|-------------|--------|----------|---------|----------|
| 0 | Fundaciones | Scaffold `mobile/`, auth móvil (riesgo #1), codegen OpenAPI→Dart, `ThemeData` (tokens), shell de navegación (bottom nav por rol), login→Home mínimo. iOS+Android. | in-progress | - | - | `plans/mobile-fase-0-fundaciones.plan.md` |
| 1 | Piso + Comanda + Contingencia | Plano de salón en vivo, comanda (grilla+carrito), enviar/editar/anular, mover/unir mesas, **cola local + sync**, **impresión ESC/POS BT**. (Modificadores del mozo diferidos = paridad web; escaneo QR-cámara → fase posterior.) | complete | - | 0 | `plans/mobile-fase-1-piso-comanda.plan.md` |
| 2 | KDS | Cola de platos en tiempo real (SSE + poll), avanzar estado por `OrderItem` (bump 1×1), demora. (Push plato-listo diferido.) | complete | with 3 | 1 | (directo, sin plan doc) |
| 3 | Caja | Cobro (efectivo/tarjeta/transferencia/QR) con monto+presets+propina, sesión de caja (abrir/cerrar + arqueo Z), reembolso, reabrir. (MP-online del cajero, split-por-ítem y AFIP diferidos.) | complete | with 2 | 1 | (directo, sin plan doc) |
| 4 | Propinas + Fichaje | Propinas por mozo/liquidación (payout), Fichaje (TimeClock: clock-in/out + turnos), hub "Más". | complete | with 5 | 3 | (directo, sin plan doc) |
| 5 | Home + Copiloto | Home con KPIs del día (GET /reports/dashboard) + Copiloto chat (POST /copilot/ask → respuesta+tabla). (Alerta/tarea/push diferidos.) | complete | with 4 | 1 | (directo) |
| 6 | Pesadas (paridad total) | **Slice 1 (consulta) hecho:** Productos, Finanzas (overview), Comprobantes en el hub "Más". Falta: edición/paridad total (Productos v2/v3, Recetas, Reportes, Insumos, Integraciones, CRM, Ajustes, AFIP emisión) con layouts adaptativos. | in-progress | - | 5 | (slice 1 directo) |

### Phase Details

**Fase 0 — Fundaciones** 🔴 primero
- **Goal**: fundación nativa validada; sin esto no se sigue.
- **Scope**: proyecto `mobile/`; **auth móvil** (secure storage + refresh sin cookie); **codegen** OpenAPI→Dart en CI; **ThemeData** con tokens (claro/oscuro por SO + toggle); shell de navegación (bottom nav por rol); login→Home mínimo contra `api.wellnod.com`.
- **Success signal**: login real por rol en iOS y Android, con paridad visual claro/oscuro, y una pantalla de punta a punta contra la API.

**Fase 1 — Piso + Comanda + Contingencia** 🟢 MVP
- **Goal**: el mozo opera el piso desde el teléfono, resistente a cortes.
- **Scope**: plano de salón, tomar/editar/anular comanda, mover/unir mesas, escaneo QR de mesa; **cola local + sync idempotente** (modo contingencia); **impresión ESC/POS por Bluetooth** (salida de cocina sin red). Reusa idempotencia+batch de [[fase-13-velocidad-operativa]].
- **Success signal**: tomar una comanda con el wifi apagado, que imprima a la comandera, y que al reconectar aparezca en el backend sin duplicar.

**Fase 2 — KDS**
- **Goal**: cocina en tiempo real.
- **Scope**: cola por SSE, avanzar estado por `OrderItem`, marcar listo, push a mozo. Optimizado para tablet fija.
- **Success signal**: el plato marcado listo en cocina notifica al mozo.

**Fase 3 — Caja**
- **Goal**: cerrar la venta desde el dispositivo.
- **Scope**: cobro (efectivo/MP/tarjeta), split, propina, apertura/cierre y arqueo Z, recibo, reembolso/anulación. Reusa `RegisterPayment`/`CashSession`.
- **Success signal**: cobro con split + arqueo Z cuadrado desde la app.

**Fase 4 — Propinas + Fichaje**
- **Goal**: cerrar la gestión del equipo.
- **Scope**: propinas por mozo/liquidación; Fichaje (TimeClock).
- **Success signal**: liquidación de propinas y fichaje de un turno desde la app.

**Fase 5 — Home + Copiloto**
- **Goal**: el dueño en la mano.
- **Scope**: Home operativo (ganancia del día, alerta, tarea de mañana) + Copiloto/Asesor (LLM, reusa infra Fase 9) + push de alertas.
- **Success signal**: el dueño consulta al copiloto y ve la ganancia del día desde el teléfono.

**Fase 6 — Pesadas (paridad total)**
- **Goal**: paridad de secciones con el web (menos la carta del comensal).
- **Scope**: Productos v2/v3 (costos/recetas), Finanzas, Reportes, Comprobantes/AFIP, Insumos/Inventario, Integraciones, CRM, Ajustes (y Panel de Plataforma si se decide incluir), con layouts adaptativos teléfono/tablet.
- **Success signal**: cada sección del web tiene su equivalente usable en mobile (editable según tamaño de pantalla).

### Parallelism Notes

El orden elegido es **Operación → dueño → pesadas** (KDS → Caja → Propinas/Fichaje → Home+Copiloto → pesadas). Técnicamente F2 (KDS) y F3 (Caja) **podrían ir en paralelo** (ambas dependen solo de F1), igual que F4 y F5; se listan en el orden de prioridad del dueño, pero se pueden solapar si hay capacidad. F6 es el long-tail hacia la paridad total y arranca después de F5.

---

## Decisions Log

| Decisión | Elección | Alternativas | Rationale |
|---|---|---|---|
| Framework | **Flutter** | React Native, nativo (Swift+Kotlin) | Fidelidad visual pixel-perfect (Skia/Impeller) + eficiencia AOT sin puente JS; los 2 criterios del dueño |
| Alcance | **Paridad con el web menos la carta del comensal** | Solo operación de piso; o todo incl. carta | El dueño quiere todas las secciones staff/dueño en mobile; la carta sigue web/PWA |
| Usuario | **Equipo + dueño del local** | Comensal | El comensal no instala nada (Carta QR web) |
| Primer valor (MVP) | **Piso + Comanda** | KDS, Caja | Mayor uso diario y mayor payoff nativo |
| Plataforma | **iOS + Android juntos** | Android primero; iOS primero | Flutter lo permite con un solo código |
| Distribución | **Stores públicas** | Enterprise/MDM; ambas | Estándar, self-service |
| Navegación | **Bottom nav por rol + "Más"** | Drawer con todo; launcher grilla | Rápido para operar de pie; el resto en "Más" |
| Offline | **Modo contingencia desde F1** | Fase dedicada posterior | Backup ante corte de luz/internet + sync al reconectar + impresión BLE local |
| Pantallas pesadas | **Paridad completa, layouts adaptativos** | Consulta en mobile; adaptativo puro | Todo editable como objetivo, sin romper UX en pantalla chica |
| Estado (fierro) | **Riverpod** (a confirmar en F0) | Bloc | Testable + inyección; default del PRD |
| Codegen (fierro) | **OpenAPI→Dart en CI** (openapi-generator/dio o swagger_parser) | Cliente a mano | DTOs siempre en sync, sin escritura manual |
| DB local (fierro) | **drift (SQLite)** | Hive/Isar | Cola transaccional para contingencia |

---

## Research Summary

**Market Context**
- Flutter y React Native son los dos líderes cross-platform; Flutter renderiza su propia UI (fidelidad e igualdad iOS/Android), RN usa vistas nativas (más deriva). Para una app operativa de todo el día en gama baja, Flutter da rendimiento más parejo (AOT nativo, sin puente JS).
- Las apps de comandas de la competencia suelen ser islas; el diferencial de Wellnod es que la app mobile se apoya en un cerebro ya integrado (cocina, caja, AFIP, finanzas, copiloto).

**Technical Context**
- El backend FastAPI ya expone OpenAPI nativo → cliente Dart por codegen.
- Idempotencia + batch + SSE (Fase 13) habilitan directo el modo contingencia (reintento seguro) y el tiempo real (KDS, plano de salón en vivo).
- RBAC + multi-tenant + RLS ya resueltos en el backend; el cliente solo manda el token.
- El plan Electron ya enfrentó el mismo tema de refresh cross-origin/split-domain → reutilizable como referencia para el auth móvil.

---

*Generado: 2026-09-02 · Flujo: `/prp-prd` (ecc) · Status: DRAFT — needs validation*

## Próximo paso

`/prp-plan .claude/PRPs/prds/mobile-app.prd.md` → selecciona la **Fase 0 (Fundaciones)** y crea el plan de implementación (auth móvil = spike del riesgo #1, codegen OpenAPI→Dart, tokens→`ThemeData`, shell de navegación, login→Home en iOS+Android).
