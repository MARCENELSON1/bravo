# Escalabilidad del backend (ruta caliente del salón)

## Problem Statement

El backend **no puede escalar horizontalmente hoy**: el bus de eventos vive en la memoria del proceso, así que una segunda réplica dejaría a la mitad de los mozos sin recibir las comandas. Y antes de llegar a ese techo, hay tres cuellos que **ya duelen con un solo local en hora pico**: cada login congela el proceso entero, el plano dispara ~25 queries por refresco (×5s por dispositivo), y el pool de conexiones tiene 15 slots que nadie eligió. El costo de no resolverlo: la app se siente lenta con el volumen actual, y cada local nuevo empeora la experiencia de todos los demás.

## Evidence

Dos auditorías independientes (capa de datos y runtime/arquitectura) sobre el código real, más medición en prod:

- **Argon2 bloquea el event loop:** `infrastructure/security/hasher.py:15-22` hashea/verifica **sin `asyncio.to_thread`**, invocado desde `authenticate.py:65`, `change_password.py:41,45`, `reset_password.py:55`. Es CPU-bound (~50-100 ms); con un solo worker congela SSE, KDS y cobros. **5-10 logins simultáneos** (cambio de turno) ya generan cola visible.
- **N+1 en órdenes:** `persistence/order_repo.py:39-47` — `[await self._load(session, row) for row in rows]` dispara una query de ítems **por cada orden**, en `list_active` (L102), `list_kds` (L89), `list_by_status` (L69), `list_open_by_session` (L118), `list_pending_qr` (L132). `GET /floor` se pollea **cada 10 s por dispositivo** (`frontend/src/hooks/use-floor.ts:14`).
- **`GetFloor` abre 4 transacciones secuenciales** (`application/floor/use_cases.py:39-59`): tables + orders + sessions + users, cada una con su `BEGIN`/`SET LOCAL`/`COMMIT`. Con 20 órdenes activas ⇒ **~24 round-trips por request**.
- **Catálogo completo en cada pago:** `application/analytics/projection.py:75,89,103` trae **todos** los productos, insumos y preparaciones del tenant solo para armar diccionarios de lookup de los pocos ítems de esa orden.
- **Pool sin dimensionar:** `persistence/database.py:32` — `create_async_engine(url, pool_pre_ping=True, future=True)` sin `pool_size`/`max_overflow` ⇒ default 5+10 = **15 conexiones**. A ~15-20 requests DB-bound concurrentes, el resto espera hasta 30 s (`pool_timeout`).
- **Índices faltantes:** `orders` tiene `tenant_id` y `status` indexados por separado pero no compuesto (`models.py:360-365`); `table_sessions` no indexa `closed_at`/`merged_into_id` (`models.py:277-306`); `payments` no indexa `created_at` pese a filtrar y ordenar por él (`models.py:449-483`); `sale_facts` no tiene `(tenant_id, occurred_at)` (`models.py:904-936`).
- **`GET /orders` sin paginar ni filtro temporal** (`order_repo.py:60-69`, expuesto en `api/v1/orders.py:121`): trae todas las órdenes del tenant desde siempre. Hoy sin callers, pero alcanzable por cualquier rol del salón.
- **Un `httpx.AsyncClient` nuevo por llamada** en 10 adapters, incluido el cobro real (`payments/mercadopago_gateway.py:78-84`): handshake TCP+TLS completo por request.
- **Push esperado in-line** en `order/use_cases.py:433` (marcar listo) y `payment/use_cases.py:484` (confirmar pago): lee tokens + OAuth + POST a FCM **antes** de responder.
- **Colas SSE sin `maxsize`** (`realtime/memory_bus.py:37,40`): un cliente que deja de drenar acumula eventos **sin techo de memoria**.
- **Bus y rate limiter in-memory** (`memory_bus.py:23`, `security/rate_limiter.py:11`): el propio código ya documenta que hay que cambiarlos por un adapter compartido para escalar. Con N réplicas, el rate limit efectivo se multiplica por N.
- **Medición en prod (tenant `bravo`):** el catálogo completo (productos + mesas + insumos + modificadores) pesa **~16 KB** — cabe holgado en caché.

## Proposed Solution

Atacar el problema en el orden en que duele, **sin tocar el dominio**: la arquitectura de ports & adapters ya existente permite resolver casi todo cambiando adapters y cableado en `container.py`.

1. **Sacar el trabajo repetido de la ruta caliente**: caché de catálogo detrás de un `CachePort` (con invalidación por escritura, no por TTL a ciegas), batch loading de los ítems de órdenes, e índices que sostengan las queries calientes.
2. **Destrabar el escalado horizontal**: reemplazar el bus in-memory y el rate limiter por adapters compartidos (Redis), que es lo único que hoy impide correr más de una réplica.
3. **Sacar lo lento del camino crítico**: extender el patrón **outbox** —que ya existe y funciona (`tax_outbox`)— al push y a los efectos de venta, más clientes HTTP reutilizados.

Se elige **Redis** sobre Memcached porque con el mismo costo operativo cubre tres necesidades (caché, rate limiter compartido, pub/sub) en vez de una. Todo va detrás de ports, con **default in-memory** para que nada cambie hasta prenderlo por env var.

## Key Hypothesis

Creemos que **cachear el catálogo, eliminar el N+1 y desbloquear el escalado horizontal** va a **sostener cientos de locales concurrentes sin degradar la experiencia del salón** para **mozos, cocina y cajeros**.
Sabremos que acertamos cuando **`GET /floor` baje de ~24 round-trips a ~3, un login deje de afectar la latencia del resto, y la API pueda correr con 2+ réplicas sin que ningún dispositivo pierda eventos**.

## What We're NOT Building

- **RabbitMQ / broker de mensajería** — evaluado y descartado: el estado vive en Postgres (el KDS lee de la DB, el SSE es solo un aviso), que es más robusto que una cola. Para el trabajo diferido alcanza el patrón **outbox** que ya existe, sin broker.
- **Cachear estado vivo** (órdenes, pagos, sesiones, stock) — es la fuente de verdad y cambia por segundo; cachearlo es cómo se rompen estos sistemas.
- **Microservicios** — el monolito modular es correcto para esta escala; los ports ya dan la separación.
- **Reescribir los repos a un unit-of-work por request** — el patrón "sesión por llamada" tiene un costo (4 transacciones en `GetFloor`) pero también un beneficio grande: **ninguna llamada externa (AFIP, MP) ocurre dentro de una transacción abierta**. No se toca sin evidencia de que el N+1 resuelto no alcanzó.
- **PgBouncer** — recién si al sumar workers/réplicas el `max_connections` de Postgres se vuelve el límite.

## Success Metrics

| Metric | Target | How Measured |
|--------|--------|--------------|
| Round-trips por `GET /floor` | ~24 → **≤ 3** | Conteo de queries (log SQL / `echo`) con 20 órdenes activas |
| Queries por pago (efectos de venta) | Catálogo completo → **solo los ids de la orden** | Fake repo que registra llamadas, en test |
| Latencia p95 del salón durante un login | Sin pico atribuible | Medición con logins concurrentes |
| Réplicas soportadas | 1 → **N** | Dos instancias locales: un evento publicado en A llega al SSE de B |
| Hit rate del caché de catálogo | ≥ 90% en operación normal | Contadores del adapter |
| Precio viejo servido tras editar | **0** | Test de invalidación + verificación manual |

## Open Questions

- [ ] ¿`GET /orders` (sin callers hoy) se pagina o se elimina? Eliminarlo es más seguro; paginarlo lo deja disponible para reportes.
- [ ] TTL de respaldo del caché: 60 s propuesto. ¿Alcanza, o conviene más corto para operaciones que tocan la DB por fuera de la app (scripts, migraciones)?
- [ ] ¿El `refetchInterval` de 10 s del frontend se alarga o se saca, ahora que el SSE avisa? (reduce 5-10× el trabajo de serialización, pero pierde la red de seguridad).
- [ ] Con snapshots de finanzas apagados (`FINANCE_SNAPSHOTS_READ=live`), ¿se prenden por tenant o se sostiene el read path con índices?
- [ ] ¿Cuántas réplicas/workers se apunta a correr? Define el dimensionado del pool y si hace falta PgBouncer.

---

## Users & Context

**Primary User**
- **Who**: el **mozo, la cocina y el cajero** en hora pico — los que sufren la latencia sin saber por qué. Secundario: el **dueño** (paga infraestructura) y quien opera el deploy.
- **Current behavior**: la app "a veces se pone lenta", sobre todo en horarios de cambio de turno (logins) y con muchas mesas abiertas.
- **Trigger**: hora pico con varios dispositivos abiertos, o un segundo local en el mismo backend.
- **Success state**: el plano y el KDS responden igual con 5 mesas que con 30, y sumar locales no degrada a los existentes.

**Job to Be Done**
Cuando **el local está lleno y todos los dispositivos están abiertos**, quiero **que la app responda igual de rápido que con el salón vacío**, para **no perder tiempo ni confianza en el sistema en el peor momento**.

**Non-Users**
El comensal de la Carta QR (su ruta ya es liviana y cacheable aparte). Los reportes y Finanzas: importan, pero no son la ruta caliente que este PRD ataca.

---

## Solution Detail

### Core Capabilities (MoSCoW)

| Priority | Capability | Rationale |
|----------|------------|-----------|
| Must | **Argon2 fuera del event loop** (`asyncio.to_thread`) | Un login no puede congelar el proceso entero |
| Must | **Batch loading de ítems de órdenes** (N+1 → 2 queries) | Es la ruta más caliente: `/floor` cada 10 s por dispositivo |
| Must | **Pool dimensionado explícitamente** | 15 conexiones por default es un techo invisible |
| Must | **4 índices compuestos/parciales** | Hoy invisibles; con historial, cada query escanea todo el tenant |
| Must | **`CachePort` + caché de catálogo con invalidación por escritura** | Saca del camino lo que se lee siempre y cambia casi nunca |
| Must | **`projection.py` deja de traer el catálogo completo** | El costo de cobrar no puede escalar con el tamaño de la carta |
| Should | **Bus compartido (Redis pub/sub o Postgres LISTEN/NOTIFY)** | Es lo ÚNICO que hoy impide correr 2+ réplicas |
| Should | **Rate limiter compartido** | Con N réplicas el límite se multiplica por N sin que nadie lo note |
| Should | **Outbox para push y efectos de venta** | Saca FCM/stock/proyección del camino crítico del cobro |
| Should | **`httpx.AsyncClient` reutilizado por adapter** | Evita handshake TLS por llamada (incluye el cobro real) |
| Could | Colas SSE con `maxsize`; client zeep de AFIP cacheado; paginar `GET /orders` | Robustez y limpieza |
| Won't | RabbitMQ; cachear estado vivo; microservicios; unit-of-work por request | Ver "What We're NOT Building" |

### MVP Scope

**Fase 1**: los tres techos de hoy (Argon2, N+1, pool) + los 4 índices + caché de catálogo + `projection.py`. Es la tanda de mayor retorno: **no requiere infraestructura nueva** (el caché arranca in-memory por default) y ataca todo lo que duele con el volumen actual.

### User Flow

- **Hora pico, hoy**: mozo abre el plano → 24 round-trips → alguien loguea → el proceso se congela 100 ms → el KDS parpadea tarde.
- **Hora pico, después**: mozo abre el plano → ~3 queries (catálogo desde caché) → un login corre en un thread aparte sin frenar a nadie → el KDS recibe el evento al instante.
- **Escalado**: se suma una réplica → ambas publican y reciben por el bus compartido → ningún dispositivo pierde eventos.

---

## Technical Approach

**Feasibility**: **HIGH**. La arquitectura ports & adapters ya existente hace que casi todo sea cambiar adapters + `container.py`, sin tocar dominio ni casos de uso. El propio código documenta el camino: *"If the API is ever scaled out, swap this adapter for a shared (Redis) one behind the same port"* (`rate_limiter.py:15-17`) y lo mismo en `memory_bus.py`.

**Architecture Notes**
- **`CachePort`** nuevo (`get`/`set`/`delete`/`bump_namespace`) con dos adapters: `InMemoryCache` (default, LRU + TTL) y `RedisCache`. Selección por `CACHE_BACKEND=memory|redis` con `providers.Selector`, igual que `push_service`/`payment_gateway`.
- **Invalidación por versionado de key**: Redis no borra por patrón, así que la key lleva una versión por `(tenant_id, entidad)`; invalidar = incrementar el contador. Atómico, sin ventana de lectura parcial; las keys viejas expiran solas.
- **Repos cacheados como decoradores** del mismo port: el dominio no se entera y se puede sacar desde el container.
- **Degradación segura**: si Redis falla o tarda (>200 ms), el adapter se comporta como cache-miss y el request va a la DB. El caché nunca es un punto de falla.
- **Outbox como patrón establecido**: `tax_outbox` ya lo implementa bien (insert local en el camino de cobro + drain con reintento). Es la plantilla para push y efectos de venta.

**Technical Risks**

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Servir datos viejos tras editar la carta | Media | Invalidación por escritura (no TTL); tests de invalidación; TTL corto de respaldo |
| Redis caído deja la app sin servicio | Baja | Adapter degrada a cache-miss + timeout corto; default `memory` |
| El batch loading cambia el orden de los ítems | Media | Respetar `ORDER BY position`; tests de equivalencia (es refactor, no cambio de comportamiento) |
| Caché desincronizado entre réplicas | Media | Redis es compartido; el pub/sub del bus también transporta invalidaciones |
| Sumar workers antes de resolver bus/rate limiter | Media | Orden explícito de fases: primero adapters compartidos, después `--workers` |
| Índices nuevos pesan en escritura | Baja | Son 4, sobre columnas ya filtradas; el parcial mantiene el índice chico |

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
| 1 | Ruta caliente + caché | `CachePort` + adapters (memoria/Redis), repos de catálogo cacheados con invalidación por escritura, `projection.py` por ids, batch loading de ítems (N+1), 4 índices | in-progress | - | - | - |
| 2 | Event loop + pool | Argon2 a `to_thread`, pool dimensionado por env, `httpx.AsyncClient` reutilizado por adapter, client zeep de AFIP cacheado | pending | with 1 | - | - |
| 3 | Escalado horizontal | Bus compartido (Redis pub/sub o Postgres LISTEN/NOTIFY) + rate limiter compartido + colas SSE con `maxsize`; recién ahí, `--workers`/réplicas | pending | - | 1, 2 | - |
| 4 | Outbox del camino crítico | Push y efectos de venta (stock, proyección) fuera del request, siguiendo el patrón de `tax_outbox` | pending | with 3 | 1 | - |
| 5 | Higiene de lectura | Paginar o eliminar `GET /orders`, `FinanceProductDetail` agregando en SQL, revisar `refetchInterval` del frontend | pending | with 3 | - | - |

### Phase Details

**Phase 1: Ruta caliente + caché**
- **Goal**: que el trabajo repetido salga del camino del salón, sin infraestructura nueva.
- **Scope**: `CachePort` + `InMemoryCache`/`RedisCache` (default memoria), decoradores de productos/insumos/preparaciones/mesas/sectores/modificadores con invalidación al escribir, `projection.py` pidiendo solo los ids de la orden, batch loading en `order_repo`, migración con los 4 índices.
- **Success signal**: `GET /floor` baja a ~3 round-trips; un test verifica que el segundo `list` no toca el repo real y que tras `save` sí; el pago deja de pedir el catálogo completo.

**Phase 2: Event loop + pool**
- **Goal**: que ninguna operación puntual congele el proceso ni agote el pool.
- **Scope**: Argon2 en `asyncio.to_thread`; `pool_size`/`max_overflow` por env var; un `httpx.AsyncClient` por adapter (cerrado en el `lifespan`); cachear el `Client` de zeep de AFIP.
- **Success signal**: logins concurrentes no producen pico de latencia en el resto; las llamadas salientes reutilizan conexión.

**Phase 3: Escalado horizontal**
- **Goal**: poder correr 2+ réplicas sin perder eventos ni aflojar el rate limit.
- **Scope**: adapter compartido del `EventBus` y del `RateLimiter`; `asyncio.Queue(maxsize=N)` con política de overflow; recién entonces habilitar workers/réplicas.
- **Success signal**: dos instancias locales; un evento publicado en A llega al SSE conectado a B; el rate limit se respeta en conjunto.

**Phase 4: Outbox del camino crítico**
- **Goal**: que cobrar y marcar listo respondan sin esperar trabajo diferible.
- **Scope**: push y efectos de venta (consumo de stock, proyección de `sale_facts`) por outbox + drain, siguiendo `tax_outbox`.
- **Success signal**: el pago responde sin esperar FCM ni la proyección; los efectos se aplican igual (con reintento si fallan).

**Phase 5: Higiene de lectura**
- **Goal**: que ninguna consulta pueda colgar un worker con el historial.
- **Scope**: `GET /orders` paginado o eliminado; `FinanceProductDetail` agregando con `func.sum` y `lines` limitado; revisar el poll del frontend.
- **Success signal**: ningún endpoint devuelve tablas completas sin cota.

### Parallelism Notes

Las **Fases 1 y 2** son independientes (una es datos/caché, la otra runtime) y pueden ir en paralelo. La **Fase 3 depende de ambas**: no tiene sentido sumar réplicas mientras cada una arrastre el N+1 y el pool sin dimensionar. Las **Fases 4 y 5** pueden ir en paralelo a la 3.

---

## Decisions Log

| Decision | Choice | Alternatives | Rationale |
|----------|--------|--------------|-----------|
| Mensajería para "encolar comandas" | **No hay broker**: el estado vive en Postgres | RabbitMQ como fuente de verdad | El KDS lee de la DB y el SSE es solo un aviso: sobrevive reinicios, un KDS que abre tarde ve lo pendiente, y hay historial. Con un broker habría dos fuentes de verdad |
| Cola de trabajo diferido | **Outbox** (ya existe: `tax_outbox`) | RabbitMQ / Celery | Da reintentos y desacople sin broker ni servicio extra; transaccional con la escritura |
| Backend de caché | **Redis** | Memcached; solo memoria | Mismo costo operativo pero cubre además rate limiter compartido y pub/sub: 3 hallazgos con un servicio |
| Ubicación del caché | **Detrás de un `CachePort`**, default in-memory | Redis directo en los repos | Tests sin infraestructura, y cambiar de backend es reemplazar un adapter |
| Invalidación | **Por escritura** (versionado de key) + TTL 60 s de respaldo | Solo TTL | Un precio editado no puede tardar en verse; el TTL cubre cambios fuera de banda |
| Qué se cachea | **Solo catálogo** (productos, insumos, preparaciones, mesas, sectores, modificadores) | Cachear también órdenes/mesas activas | El estado vivo es la fuente de verdad y cambia por segundo |
| Bus compartido | **Redis pub/sub o Postgres LISTEN/NOTIFY** (a decidir en Fase 3) | Broker dedicado | Ambos resuelven el cruce entre procesos sin infra nueva relevante; LISTEN/NOTIFY no agrega servicio, Redis ya estaría |
| Orden de trabajo | **Ruta caliente primero, escalado después** | Escalar horizontalmente ya | Sumar réplicas con N+1 y pool sin dimensionar multiplica el problema en vez de resolverlo |
| Patrón "sesión por llamada de repo" | **Se mantiene** | Unit-of-work por request | Cuesta round-trips, pero garantiza que ninguna llamada externa (AFIP/MP) ocurra dentro de una transacción abierta |

---

## Research Summary

**Market Context**
- El patrón de la industria para POS de hospitality es **estado en la base + notificación liviana** (lo que ya hace BRAVO), no cola como fuente de verdad: un KDS tiene que poder reiniciarse y recuperar todo lo pendiente.
- **Outbox** es el patrón estándar para efectos secundarios transaccionales (facturación, notificaciones) sin agregar un broker.
- Cachear catálogo con invalidación por escritura es práctica común en e-commerce/POS: alta relación lectura/escritura y datos chicos.

**Technical Context**
- Dos auditorías independientes coincidieron en el diagnóstico y en que **no hay nada mal diseñado**: los problemas son de configuración y de rutas calientes, no estructurales.
- Lo que está **bien resuelto y no se toca**: RLS con `SET LOCAL` (seguro con pooling, sin fugas entre requests); ninguna llamada externa dentro de transacción; cache del ticket AFIP con lock (sin thundering herd); idempotencia de pagos y de consumo de stock; DI con `Singleton` para lo caro y `Factory` para lo liviano; sin `requests`/`time.sleep` en toda la base; `GetFloor` sin N+1 por mesa (3 queries batch).
- Medición en prod (`bravo`): catálogo completo ~16 KB ⇒ cachear en memoria es viable incluso con miles de tenants.

---

*Generated: 2026-09-05*
*Status: DRAFT - needs validation*
