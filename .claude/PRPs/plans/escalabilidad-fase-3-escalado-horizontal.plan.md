# Plan: Escalabilidad Fase 3 — escalado horizontal (bus y rate limiter compartidos)

## Summary

Hoy la API **no puede correr con más de un proceso**: el bus de eventos vive en la memoria de la instancia, así que un mozo conectado a la réplica A nunca recibiría lo que publica la B — el KDS y el plano dejarían de actualizarse para la mitad de la gente. Esta fase pone el bus y el rate limiter detrás de adapters compartidos (Redis), acota las colas SSE, y recién entonces habilita sumar réplicas.

## User Story

Como **dueño que suma locales**, quiero **que la API pueda correr en varias instancias sin que nadie pierda comandas**, para **crecer sin degradar el servicio de los locales que ya están**.

## Problem → Solution

**Hoy:** `InMemoryEventBus` reparte eventos entre suscriptores **del mismo proceso** (`memory_bus.py:23-40`). Con 2 réplicas, un `order.ready` publicado en A no llega al SSE conectado a B. Además el `InMemoryRateLimiter` cuenta por proceso: con N réplicas, el límite efectivo se multiplica por N. Y las colas SSE no tienen `maxsize`: un cliente que deja de drenar acumula eventos sin techo.

**Después:** ambos adapters usan Redis (que ya se agregó como dependencia en la Fase 1), las colas tienen tope con política de descarte, y la API puede escalar horizontalmente con el SSE funcionando.

## Metadata

- **Complexity**: Medium
- **Source PRD**: `.claude/PRPs/prds/escalabilidad-backend.prd.md`
- **PRD Phase**: Fase 3 — Escalado horizontal
- **Estimated Files**: ~10 (2 adapters nuevos, 1 conexión compartida, config, container, memory_bus, tests)
- **Depends on**: Fase 1 (`e50a87c`, trajo Redis y el patrón `Selector`) y Fase 2 (`2874a86`)

---

## UX Design

**Internal change — no user-facing UX transformation.** Nada cambia para el usuario mientras siga corriendo una sola instancia; habilita que sumar instancias no rompa el realtime.

### Interaction Changes

| Touchpoint | Before | After | Notes |
|---|---|---|---|
| KDS con 2+ réplicas | La mitad de los dispositivos no recibe eventos | Todos reciben | El motivo de la fase |
| Rate limit de la Carta QR | Se multiplica por N réplicas | Límite real compartido | Anti-abuso vuelve a ser efectivo |
| Cliente SSE con mala señal | Su cola crece sin techo (memoria) | Cola acotada, descarta lo viejo | El cliente se recupera con su poll |

---

## Mandatory Reading

| Priority | File | Lines | Why |
|---|---|---|---|
| P0 | `app/infrastructure/realtime/memory_bus.py` | todo | El adapter a espejar; su docstring ya anticipa este cambio |
| P0 | `app/domain/realtime/ports.py` | 8-43 | `DomainEvent`, `Subscription`, `EventBus` — el contrato a respetar |
| P0 | `app/presentation/api/v1/realtime.py` | 44-67 | Cómo se consume: `subscribe()` → `await sub.get()` con timeout → `sub.close()` |
| P0 | `app/infrastructure/cache/redis_cache.py` | todo | **Patrón de la casa para Redis**: fail-open, timeouts, cómo se crea el cliente (Fase 1) |
| P0 | `app/domain/shared/rate_limiter.py` | todo | Port de una sola función: `check(key, limit, window_seconds)` |
| P1 | `app/infrastructure/security/rate_limiter.py` | 11-35 | La implementación in-memory (sliding window) a espejar |
| P1 | `app/config.py` | — | `cache_backend`/`redis_url` (Fase 1) y el patrón de fail-fast |
| P1 | `app/container.py` | — | `providers.Selector` para elegir adapter por env (ver `push_service`, `cache`) |
| P2 | `app/infrastructure/http/client.py` | todo | Patrón de recurso de proceso con `aclose()` en el `lifespan` (Fase 2) |
| P2 | `app/main.py` | — | Dónde engancharlo al `lifespan` |

## External Documentation

| Topic | Source | Key Takeaway |
|---|---|---|
| Redis Pub/Sub | docs | Fire-and-forget: **no persiste**. Correcto acá — el SSE ya es un aviso y el cliente refetchea de la DB |
| `redis.asyncio` PubSub | docs | `pubsub()` requiere su **propia conexión**; se lee con `get_message`/`listen` en una tarea aparte |
| Sliding window en Redis | patrón | `ZADD` + `ZREMRANGEBYSCORE` + `ZCARD` en un `pipeline`/Lua para que sea atómico |

---

## Patterns to Mirror

### REDIS_ADAPTER_FAIL_OPEN (Fase 1 — el patrón de la casa)
```python
# SOURCE: app/infrastructure/cache/redis_cache.py
# Timeout corto y cualquier error de Redis degrada a "no hay dato" en vez de
# romper el request: un Redis caído deja el sistema lento, no roto.
```

### SELECTOR_BY_ENV
```python
# SOURCE: app/container.py (push_service, cache)
providers.Selector(config.provided.<flag>, memory=..., redis=...)
```

### IN_MEMORY_BUS (el contrato que hay que respetar)
```python
# SOURCE: app/infrastructure/realtime/memory_bus.py:32-50
# subscribe() devuelve una Subscription con get() y close();
# publish() reparte SOLO a los suscriptores del mismo tenant_id.
```

### PROCESS_RESOURCE_LIFESPAN
```python
# SOURCE: app/infrastructure/http/client.py + app/main.py (Fase 2)
# Recurso de proceso creado como Singleton y cerrado una vez en el lifespan.
```

---

## Files to Change

| File | Action | Justification |
|---|---|---|
| `app/infrastructure/realtime/redis_bus.py` | CREATE | `RedisEventBus`: publish → `PUBLISH`, subscribe → cola local alimentada por una tarea que escucha el canal del tenant |
| `app/infrastructure/realtime/memory_bus.py` | UPDATE | `asyncio.Queue(maxsize=N)` + política de descarte |
| `app/infrastructure/security/redis_rate_limiter.py` | CREATE | Sliding window compartido con `ZADD`/`ZREMRANGEBYSCORE`/`ZCARD` atómico |
| `app/infrastructure/redis/connection.py` | CREATE | Conexión Redis compartida por proceso (la usan caché, bus y rate limiter) |
| `app/infrastructure/cache/redis_cache.py` | UPDATE | Recibir la conexión compartida en vez de crear la suya |
| `app/config.py` | UPDATE | `EVENT_BUS_BACKEND` y `RATE_LIMITER_BACKEND` (`memory|redis`, default `memory`) + fail-fast si `redis` sin `REDIS_URL` |
| `app/container.py` | UPDATE | `Selector` para bus y rate limiter; conexión Redis como `Singleton` |
| `app/main.py` | UPDATE | Cerrar la conexión Redis en el `lifespan` |
| `tests/unit/test_redis_bus.py` | CREATE | Contrato del bus + aislamiento por tenant + fail-open |
| `tests/unit/test_redis_rate_limiter.py` | CREATE | Ventana deslizante, límite compartido, fail-open |
| `tests/unit/test_memory_bus.py` | UPDATE/CREATE | Comportamiento con `maxsize` (descarte, no bloqueo) |

## NOT Building

- **No se cambia el contrato del `EventBus`** — `publish`/`subscribe`/`get`/`close` quedan igual: el SSE no se toca.
- **No se agrega persistencia ni entrega garantizada** de eventos: el SSE es un aviso, el estado vive en Postgres y el cliente refetchea. (Y para app cerrada ya está el push FCM.)
- **No se toca el outbox de push ni los efectos de venta** — Fase 4.
- **No se pagina `GET /orders`** — Fase 5.
- **No se sube `--workers` en el Dockerfile en este commit**: primero se valida el bus compartido con dos instancias locales; habilitarlo es el paso final y explícito.
- **No se migra el caché a "invalidación por pub/sub"**: con Redis el caché ya es compartido, así que no hace falta.

---

## Step-by-Step Tasks

### Task 1: Conexión Redis compartida
- **ACTION**: Un solo cliente Redis por proceso, reutilizado por caché, bus y rate limiter.
- **IMPLEMENT**: `app/infrastructure/redis/connection.py` con un proveedor que exponga el cliente (`redis.asyncio.from_url` con timeouts explícitos) y `aclose()`. `Singleton` en el container, cerrado en el `lifespan`.
- **MIRROR**: `PROCESS_RESOURCE_LIFESPAN` (`http/client.py` de la Fase 2).
- **GOTCHA**: **PubSub necesita su propia conexión** — no se puede usar la misma que sirve `GET`/`SET` mientras escucha. El proveedor tiene que poder dar una conexión dedicada para el bus.
- **VALIDATE**: `poetry run pytest tests/unit -k "redis" -q`.

### Task 2: `RedisEventBus`
- **ACTION**: Bus que cruza procesos, respetando el contrato actual.
- **IMPLEMENT**: `publish` serializa el `DomainEvent` a JSON y hace `PUBLISH` al canal del tenant (ej. `events:{tenant_id}`). `subscribe(tenant_id)` devuelve una `Subscription` con una `asyncio.Queue` **acotada**, alimentada por una tarea que escucha ese canal; `close()` cancela la suscripción y libera la conexión.
- **MIRROR**: `IN_MEMORY_BUS` (contrato) + `REDIS_ADAPTER_FAIL_OPEN` (errores).
- **IMPORTS**: `redis.asyncio`, `json`, `asyncio`, `DomainEvent`/`Subscription`/`EventBus`.
- **GOTCHA**: **Aislamiento por tenant**: un canal por tenant, nunca uno global filtrando en el cliente. Si Redis se cae, `publish` no debe romper el request que lo disparó (un evento perdido es una molestia; un cobro fallido, no). El `payload` viaja como JSON — verificar que todos los payloads actuales sean serializables (hoy son `str`/`int`).
- **VALIDATE**: Test de contrato: publicar en una instancia del bus y recibir en otra instancia distinta (simulando dos procesos).

### Task 3: Colas SSE acotadas
- **ACTION**: Que un consumidor lento no consuma memoria sin techo.
- **IMPLEMENT**: `asyncio.Queue(maxsize=N)` (ej. 100) en ambos buses. Al llenarse: **descartar el evento más viejo** y encolar el nuevo (el cliente se recupera con su refetch).
- **GOTCHA**: **Nunca usar `await queue.put()`** en `publish`: bloquearía al publicador (el request del mozo) por culpa de un cliente lento. `put_nowait` + manejo de `QueueFull`.
- **VALIDATE**: Test que llena la cola y verifica que `publish` no bloquea y que se conserva lo más nuevo.

### Task 4: `RedisRateLimiter`
- **ACTION**: Límite real compartido entre réplicas.
- **IMPLEMENT**: Sliding window con sorted set: `ZREMRANGEBYSCORE` (limpia lo viejo) + `ZCARD` (cuenta) + `ZADD` (registra) + `EXPIRE`, todo en un `pipeline` atómico. Misma semántica que el in-memory: la (limit+1)-ésima dentro de la ventana levanta `RateLimited`.
- **MIRROR**: `app/infrastructure/security/rate_limiter.py:24-35` (semántica) + `REDIS_ADAPTER_FAIL_OPEN`.
- **GOTCHA**: Decidir explícitamente el modo de falla: si Redis está caído, **permitir** (fail-open) es lo correcto acá — es un guard anti-abuso, no una barrera de seguridad; bloquear pedidos legítimos sería peor. Documentarlo en el docstring.
- **VALIDATE**: Test de ventana (N pasan, N+1 falla, tras la ventana vuelve a pasar) y de límite compartido entre dos instancias.

### Task 5: Config + wiring
- **ACTION**: Elegir adapter por env, con default seguro.
- **IMPLEMENT**: `EVENT_BUS_BACKEND` y `RATE_LIMITER_BACKEND` (`memory|redis`, **default `memory`**) en `config.py`, con fail-fast si `redis` sin `REDIS_URL`. `Selector` en `container.py`.
- **MIRROR**: `SELECTOR_BY_ENV`.
- **GOTCHA**: El fail-fast de `cache_backend` (Fase 1) quedó dentro de `_reject_insecure_production`, que **retorna temprano en dev** — o sea que no valida ahí. Poner estas validaciones donde sí corran siempre, y de paso dejar reportado el caso anterior (no arreglarlo en esta fase).
- **VALIDATE**: Test que con `redis` sin URL levante error, y que el `Selector` devuelva el adapter correcto.

### Task 6: Verificación de dos procesos
- **ACTION**: Probar de verdad lo que motiva la fase.
- **IMPLEMENT**: Levantar **dos instancias locales** de la API contra el mismo Redis y Postgres; abrir un SSE en la instancia A; disparar una acción en la B (marchar una comanda); confirmar que el evento llega a A.
- **GOTCHA**: Sin esto, la fase no está verificada — un test unitario con dos objetos en el mismo proceso **no prueba** que cruce procesos.
- **VALIDATE**: Documentar el resultado (comando + evidencia) en el resumen final.

### Task 7: Habilitar réplicas (último, explícito)
- **ACTION**: Recién con lo anterior verde, permitir escalar.
- **IMPLEMENT**: Documentar en el PRD/README qué hay que setear en Railway (`EVENT_BUS_BACKEND=redis`, `RATE_LIMITER_BACKEND=redis`, `CACHE_BACKEND=redis`, `REDIS_URL`) y recién ahí subir réplicas/workers.
- **GOTCHA**: **No cambiar el `CMD` del Dockerfile en este commit.** Sumar workers sin Redis prendido rompe el realtime. Que quede como paso operativo consciente.
- **VALIDATE**: Instrucciones claras; nada se rompe si no se prende (default `memory`).

---

## Testing Strategy

### Unit Tests

| Test | Input | Expected Output | Edge Case? |
|---|---|---|---|
| Bus: publish/subscribe cruza instancias | Evento en bus A | Llega a bus B | ✅ **el motivo de la fase** |
| Bus: aislamiento por tenant | Evento del tenant X | El suscriptor de Y **no** lo recibe | ✅ seguridad |
| Bus: Redis caído | `publish` con Redis abajo | No rompe el request | ✅ |
| Bus: payload serializable | Evento con payload real | Sobrevive el round-trip JSON | ✅ |
| Cola llena | maxsize+10 eventos | `publish` no bloquea; se conserva lo nuevo | ✅ |
| `close()` libera | subscribe + close | Sin tareas ni conexiones colgadas | ✅ |
| Rate limit: ventana | N hits, N+1 | El N+1 levanta `RateLimited` | — |
| Rate limit: compartido | Hits desde 2 instancias | Cuentan al mismo total | ✅ **el motivo** |
| Rate limit: Redis caído | Redis abajo | Permite (fail-open), documentado | ✅ |
| Config: `redis` sin URL | Settings inválidos | Error al arrancar | ✅ |

### Edge Cases Checklist
- [ ] Redis cae **con** streams SSE abiertos (¿reconecta o cierra limpio?)
- [ ] Dos suscriptores del mismo tenant reciben ambos
- [ ] Un tenant sin suscriptores: `publish` no falla
- [ ] `close()` durante un `get()` en curso
- [ ] Reconexión de Redis tras una caída transitoria

---

## Validation Commands

### Static Analysis
```bash
cd backend && poetry run ruff check app tests
```
EXPECT: sin errores **nuevos** (preexistentes: `me.py` I001 — no tocar — y `test_e2e_finance.py` E501 ×2)

### Full Test Suite
```bash
cd backend && poetry run pytest -q -p no:warnings
```
EXPECT: exit 0, sin regresiones (baseline: **783** tests)

### Database Validation
```bash
cd backend && poetry run alembic current
```
EXPECT: `0055_hot_path_indexes` (esta fase **no** agrega migraciones)

### Manual Validation (Task 6 — imprescindible)
- [ ] Dos instancias locales + Redis: evento publicado en una llega al SSE de la otra
- [ ] Con `EVENT_BUS_BACKEND=memory` (default) todo sigue funcionando igual que hoy
- [ ] Rate limit respetado en conjunto por las dos instancias

---

## Acceptance Criteria
- [ ] `RedisEventBus` cumple el contrato sin tocar `realtime.py`
- [ ] Aislamiento por tenant verificado con test
- [ ] Colas acotadas: un consumidor lento no bloquea al publicador ni crece sin techo
- [ ] `RedisRateLimiter` con misma semántica que el in-memory, y compartido
- [ ] Default `memory` en todo: **nada cambia hasta prenderlo**
- [ ] Redis caído degrada (no rompe cobros ni pedidos)
- [ ] **Verificación real de dos procesos documentada**
- [ ] Suite completa verde

## Completion Checklist
- [ ] Código en inglés; `domain` sin frameworks
- [ ] `me.py`, `auth.py`, `.mcp.json` intactos
- [ ] Sin scope creep (outbox y paginación son Fases 4 y 5)
- [ ] Instrucciones de Railway documentadas, sin cambiar el `CMD`

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Fuga de eventos entre tenants | Baja | **Alto (privacidad)** | Un canal por tenant + test de aislamiento explícito |
| Redis caído deja el salón sin realtime | Media | Medio | Fail-open + el cliente ya refetchea por poll; documentar el modo degradado |
| Tarea de escucha filtrada por suscripción no cerrada | Media | Medio | `close()` cancela la tarea; test de limpieza |
| `publish` bloquea por un cliente lento | Media | Alto | `put_nowait` + descarte; nunca `await put()` |
| Prender workers sin Redis | Media | **Alto (rompe el realtime)** | Default `memory`, `CMD` sin tocar, y el paso operativo documentado |
| Semántica del rate limit distinta a la in-memory | Baja | Bajo | Tests de paridad entre ambos adapters |

## Notes

- **Por qué Redis pub/sub y no Postgres LISTEN/NOTIFY**: se evaluaron ambos en el PRD. Como Redis ya entró en la Fase 1 para el caché, usarlo también acá evita sumar otro mecanismo; LISTEN/NOTIFY habría evitado el servicio, pero ese barco ya zarpó con la decisión del caché.
- **Fire-and-forget es correcto acá**: el SSE nunca fue la fuente de verdad — el KDS lee de Postgres y el cliente refetchea. Un evento perdido se recupera solo; por eso no hace falta entrega garantizada (y por eso tampoco hacía falta un broker).
- **Esta fase no acelera nada**: habilita crecer. La mejora de velocidad ya vino en las Fases 1 y 2.
