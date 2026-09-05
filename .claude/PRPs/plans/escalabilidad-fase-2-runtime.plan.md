# Plan: Escalabilidad Fase 2 — event loop, pool y clientes HTTP

## Summary

Sacar del camino los tres problemas de **runtime** que hoy frenan a todos los usuarios a la vez: el hasheo de contraseñas que congela el proceso entero en cada login, el pool de conexiones que nadie dimensionó (15 slots por default), y los clientes HTTP que abren una conexión TLS nueva en cada llamada saliente. Ninguno requiere infraestructura nueva.

## User Story

Como **mozo/cajero en hora pico**, quiero **que un compañero pueda loguearse sin que se me congele la app**, para **no perder segundos justo cuando el salón está lleno**.

## Problem → Solution

**Hoy:** un login corre Argon2 (CPU-bound, ~50-100 ms) directamente en el event loop de un proceso único → **congela SSE, KDS y cobros para todos**. Además, ~15-20 requests concurrentes agotan el pool y el resto espera hasta 30 s; y cada llamada a MercadoPago/FCM/AFIP paga un handshake TLS completo.

**Después:** el hasheo corre en un thread aparte (el loop sigue atendiendo), el pool está dimensionado a propósito por env var, y las llamadas salientes reutilizan conexión.

## Metadata

- **Complexity**: Medium
- **Source PRD**: `.claude/PRPs/prds/escalabilidad-backend.prd.md`
- **PRD Phase**: Fase 2 — Event loop + pool
- **Estimated Files**: ~18 (1 port, 1 adapter, 6 casos de uso, 1 database, 10 adapters HTTP, tests)

---

## UX Design

**Internal change — no user-facing UX transformation.** El usuario no ve nada nuevo; percibe que la app deja de "trabarse" cuando alguien loguea.

### Interaction Changes

| Touchpoint | Before | After | Notes |
|---|---|---|---|
| Login de un usuario | Congela el proceso ~50-100 ms para **todos** | Corre en thread; el resto sigue respondiendo | El login en sí tarda lo mismo |
| Salón con muchos dispositivos | A ~15-20 requests DB concurrentes, el resto espera (hasta 30 s) | Pool dimensionado a propósito | Configurable por env |
| Cobro con MercadoPago | Handshake TCP+TLS por llamada | Conexión reutilizada | ~50-150 ms menos por llamada |

---

## Mandatory Reading

| Priority | File | Lines | Why |
|---|---|---|---|
| P0 | `app/domain/identity/ports.py` | 33-38 | El port `PasswordHasher` es **sincrónico**; hay que volverlo async |
| P0 | `app/infrastructure/security/hasher.py` | todo | El adapter a corregir (23 líneas) |
| P0 | `app/infrastructure/persistence/database.py` | 30-40 | Dónde se crea el engine, sin dimensionar |
| P0 | `app/config.py` | — | Patrón de settings + `_fail_fast` (ver `cache_backend`, agregado en Fase 1) |
| P1 | `app/application/identity/authenticate.py` | 65 | Caller de `verify` — el más caliente |
| P1 | `app/infrastructure/payments/mercadopago_gateway.py` | 78-84, 133, 174 | Patrón de cliente HTTP por llamada (**camino de cobro real**) |
| P1 | `app/container.py` | ~418 | Cómo se cablea `Database` y los adapters (`Singleton` vs `Factory`) |
| P2 | `app/infrastructure/invoicing/afip_wsaa.py` | 95-136 | Cache + `asyncio.Lock` bien hechos: **el patrón a imitar** |
| P2 | `app/main.py` | — | Si existe `lifespan`, es donde cerrar los clientes HTTP |

## External Documentation

| Topic | Source | Key Takeaway |
|---|---|---|
| `asyncio.to_thread` | stdlib | Corre una función sync en el executor por default; el loop sigue libre |
| SQLAlchemy async pool | docs | `pool_size` + `max_overflow` = conexiones máximas por proceso; `pool_timeout` es la espera antes de fallar |
| `httpx.AsyncClient` | docs | Reutilizar el cliente mantiene keep-alive; **hay que cerrarlo** (`aclose`) al apagar |

---

## Patterns to Mirror

### PORT_ASYNC (así se ve un port async del proyecto)
```python
# SOURCE: app/domain/notification/ports.py
class NotificationService(ABC):
    @abstractmethod
    async def notify_user(self, *, tenant_id: str, user_id: str, message: PushMessage) -> None: ...
```

### CACHE_WITH_LOCK (cache + lock, ya resuelto en AFIP — imitar para el cliente HTTP)
```python
# SOURCE: app/infrastructure/invoicing/afip_wsaa.py:95-136
# Cachea el ticket por CUIT y serializa la renovación con asyncio.Lock
# → sin thundering herd cuando varios requests lo necesitan a la vez.
```

### SETTINGS_WITH_FAILFAST
```python
# SOURCE: app/config.py (patrón de la Fase 1)
cache_backend: Literal["memory", "redis"] = "memory"
redis_url: str = "redis://localhost:6379/0"
# ...
if self.cache_backend == "redis" and not self.redis_url:
    raise ValueError("CACHE_BACKEND=redis requiere REDIS_URL")
```

### DI_SINGLETON_VS_FACTORY
```python
# SOURCE: app/container.py:417-432
# Singleton para lo caro/con estado (engine, hasher, event bus);
# Factory para casos de uso y repos (por request).
```

---

## Files to Change

| File | Action | Justification |
|---|---|---|
| `app/domain/identity/ports.py` | UPDATE | `PasswordHasher.hash/verify` pasan a `async` |
| `app/infrastructure/security/hasher.py` | UPDATE | Envolver Argon2 en `asyncio.to_thread` |
| `app/application/identity/authenticate.py` | UPDATE | `await` en `verify` (L65) |
| `app/application/identity/change_password.py` | UPDATE | `await` en `verify` (L41) y `hash` (L45) |
| `app/application/identity/reset_password.py` | UPDATE | `await` en `hash` (L55) |
| `app/application/identity/accept_invitation.py` | UPDATE | `await` en `hash` (L49) |
| `app/application/identity/onboard_tenant.py` | UPDATE | `await` en `hash` (L80) |
| `app/infrastructure/persistence/database.py` | UPDATE | `pool_size`/`max_overflow`/`pool_timeout`/`pool_recycle` |
| `app/config.py` | UPDATE | Settings del pool (con defaults sanos) |
| `app/container.py` | UPDATE | Pasar settings del pool a `Database`; cablear el cliente HTTP compartido |
| `app/infrastructure/http/client.py` | CREATE | `HttpClientProvider`: un `AsyncClient` compartido, con `aclose()` |
| 10 adapters (`payments/`, `notification/`, `tax/`, `marketing/`, `email/`, `billing/`) | UPDATE | Reutilizar el cliente en vez de crear uno por llamada |
| `app/infrastructure/invoicing/afip_wsaa.py`, `afip_invoicing.py` | UPDATE | Cachear el `Client` de zeep (hoy re-descarga el WSDL en cada llamada) |
| `app/main.py` | UPDATE | Cerrar el cliente HTTP en el `lifespan` |
| Tests (varios) | UPDATE/CREATE | Fakes de hasher pasan a async; test de no-bloqueo; test del cliente compartido |

## NOT Building

- **No se toca el `EventBus` ni el `RateLimiter`** — son Fase 3.
- **No se agregan `--workers` ni réplicas** — sin bus compartido, sumar workers rompe el SSE. Fase 3.
- **No se mueve el push ni los efectos de venta a outbox** — Fase 4.
- **No se pagina `GET /orders`** — Fase 5.
- **No se cambia el algoritmo de hashing** ni sus parámetros: solo dónde corre. Los hashes existentes siguen validando.
- **No se introduce un `ThreadPoolExecutor` dedicado** salvo que el default demuestre ser cuello (AFIP ya usa `to_thread`; medir antes).

---

## Step-by-Step Tasks

### Task 1: `PasswordHasher` pasa a async
- **ACTION**: Cambiar el port y su adapter para que el hasheo no bloquee el loop.
- **IMPLEMENT**: En `app/domain/identity/ports.py:33-38`, `hash`/`verify` pasan a `async def`. En `hasher.py`, envolver ambas llamadas de Argon2 en `await asyncio.to_thread(...)`, manteniendo el manejo de excepciones (`VerifyMismatchError`, `VerificationError`, `InvalidHashError` ⇒ `False`).
- **MIRROR**: `PORT_ASYNC` (arriba).
- **IMPORTS**: `import asyncio` en el adapter.
- **GOTCHA**: `to_thread` propaga las excepciones del hilo — el `try/except` sigue funcionando igual, pero tiene que envolver el `await`, no la llamada interna. **No cambiar los parámetros de Argon2**: los hashes ya guardados deben seguir validando.
- **VALIDATE**: `poetry run pytest tests/unit -k "hash or password or auth" -q`.

### Task 2: `await` en los 6 call sites
- **ACTION**: Actualizar los casos de uso que llaman al hasher.
- **IMPLEMENT**: `authenticate.py:65`, `change_password.py:41,45`, `reset_password.py:55`, `accept_invitation.py:49`, `onboard_tenant.py:80` — agregar `await`. Todos ya están en métodos `async`, no hace falta cambiar firmas.
- **GOTCHA**: `user.set_password(self._hasher.hash(p))` pasa a `user.set_password(await self._hasher.hash(p))` — **el `await` va adentro**, no envolviendo `set_password`.
- **VALIDATE**: `poetry run ruff check app` + la suite de identity.

### Task 3: Fakes de hasher en tests
- **ACTION**: Adaptar los dobles de prueba al port async.
- **IMPLEMENT**: Buscar (`grep -rn "PasswordHasher\|hasher" tests/`) los fakes y volver `hash`/`verify` async.
- **GOTCHA**: Si algún test llama al hasher directo sin `await`, va a comparar contra una corrutina y pasar/fallar de forma engañosa. Revisar los asserts.
- **VALIDATE**: `poetry run pytest -q -p no:warnings` completo.

### Task 4: Test de no-bloqueo del event loop
- **ACTION**: Probar la regresión que motiva la tarea.
- **IMPLEMENT**: Test async que lanza un `hash` (o varios con `asyncio.gather`) y en paralelo corre una tarea que incrementa un contador con `await asyncio.sleep(0)`; verificar que el contador avanzó **durante** el hasheo. Con el código viejo (sync) el contador quedaría en 0.
- **GOTCHA**: Que no dependa de tiempos exactos (test flaky). Usar el patrón "el loop siguió avanzando", no "tardó menos de X ms".
- **VALIDATE**: El test falla si se revierte el Task 1.

### Task 5: Dimensionar el pool
- **ACTION**: Configurar el engine a propósito, por env var.
- **IMPLEMENT**: En `config.py`, `db_pool_size` (default 10), `db_max_overflow` (default 20), `db_pool_timeout` (default 10 s), `db_pool_recycle` (default 1800 s). En `database.py:32`, pasarlos a `create_async_engine`, conservando `pool_pre_ping=True`. `Database.__init__` los recibe como parámetros (no lee settings directo: es infraestructura, se cablea en el container).
- **MIRROR**: `SETTINGS_WITH_FAILFAST`.
- **GOTCHA**: `pool_timeout` bajo (10 s) es **mejor** que el default de 30: falla rápido y visible en vez de colgar el request. Documentar en el docstring que `pool_size + max_overflow` × workers no puede superar el `max_connections` de Postgres.
- **VALIDATE**: `poetry run python -c "from app.container import Container; ..."` o un test que instancie `Database` y verifique los parámetros del pool.

### Task 6: Cliente HTTP compartido
- **ACTION**: Un `httpx.AsyncClient` por proceso, reutilizado por todos los adapters.
- **IMPLEMENT**: `app/infrastructure/http/client.py` con un proveedor que exponga el cliente (timeouts explícitos, límites de conexión) y `aclose()`. Cablearlo como `Singleton` en `container.py`. Cerrarlo en el `lifespan` de `app/main.py`.
- **GOTCHA**: Los adapters que hoy **bakean headers en el constructor** del cliente (ej. `Authorization` por tenant en MercadoPago) **no pueden compartirlo así**: hay que pasar los headers **por request** (`client.post(url, headers=...)`). Revisar uno por uno — **mezclar credenciales de tenants sería un bug de seguridad**.
- **VALIDATE**: `poetry run pytest tests -k "mercadopago or fcm or resend or taxjar" -q`.

### Task 7: Migrar los 10 adapters
- **ACTION**: Reemplazar `async with httpx.AsyncClient() as client:` por el cliente compartido.
- **IMPLEMENT**: En orden de importancia: `payments/mercadopago_gateway.py` (cobro real), `notification/fcm_service.py`, `payments/mercadopago_oauth.py`, `email/resend_sender.py`, `tax/taxjar_*.py` (3), `marketing/twenty_lead_gateway.py`, `billing/*.py` (2).
- **GOTCHA**: **No cerrar** el cliente compartido dentro de un adapter (`async with` lo cerraría al salir). Usarlo directamente y dejar el cierre al `lifespan`.
- **VALIDATE**: Suite completa + `grep -rn "httpx.AsyncClient(" app/infrastructure/` debería devolver solo el proveedor.

### Task 8: Cachear el cliente zeep de AFIP
- **ACTION**: Dejar de re-descargar el WSDL en cada llamada.
- **IMPLEMENT**: En `afip_wsaa.py:131` y `afip_invoicing.py:66`, cachear el `Client` por (servicio, entorno) con `asyncio.Lock` para la creación.
- **MIRROR**: `CACHE_WITH_LOCK` — el mismo archivo ya lo hace bien para el ticket de acceso.
- **GOTCHA**: `Client` de zeep **no es async**: se sigue creando dentro de `asyncio.to_thread`. El lock protege la creación, no el uso.
- **VALIDATE**: Tests de facturación existentes (con el fake de AFIP).

---

## Testing Strategy

### Unit Tests

| Test | Input | Expected Output | Edge Case? |
|---|---|---|---|
| `hash` es awaitable y produce hash válido | password | `verify(password, hash) is True` | — |
| `verify` con password incorrecta | password errónea | `False` (no excepción) | ✅ |
| `verify` con hash corrupto | `"no-es-un-hash"` | `False` (`InvalidHashError` capturado) | ✅ |
| Hashes viejos siguen validando | hash pre-cambio | `True` | ✅ regresión |
| El loop no se bloquea durante el hasheo | `gather(hash, tick)` | el contador avanzó | ✅ **la regresión que motiva todo** |
| Pool configurado | settings | engine con `pool_size`/`max_overflow` esperados | — |
| Cliente HTTP compartido | 2 llamadas | misma instancia de cliente | — |
| Headers por request, no por cliente | 2 tenants | cada request lleva su `Authorization` | ✅ **seguridad** |

### Edge Cases Checklist
- [ ] Password vacía o muy larga
- [ ] Hash corrupto / de otro algoritmo
- [ ] Varios logins concurrentes (`gather`) no se pisan
- [ ] Dos tenants distintos llamando a MercadoPago en paralelo: **credenciales no se mezclan**
- [ ] Cierre del cliente HTTP con requests en vuelo (lifespan)
- [ ] Pool agotado ⇒ falla rápido y claro (no cuelga 30 s)

---

## Validation Commands

### Static Analysis
```bash
cd backend && poetry run ruff check app tests
```
EXPECT: sin errores nuevos (los preexistentes en `me.py` y `test_e2e_finance.py` no cuentan — **no tocar `me.py`**)

### Unit Tests
```bash
cd backend && poetry run pytest tests/unit -q -p no:warnings
```
EXPECT: todos pasan

### Full Test Suite
```bash
cd backend && poetry run pytest -q -p no:warnings
```
EXPECT: exit 0, sin regresiones (baseline: 768 tests en verde)

### Database Validation
```bash
cd backend && poetry run alembic current
```
EXPECT: `0055_hot_path_indexes` (esta fase **no** agrega migraciones)

### Manual Validation
- [ ] Login contra prod sigue funcionando con un usuario existente (hashes viejos válidos)
- [ ] Un cobro con MercadoPago sigue andando (cliente compartido, headers por request)
- [ ] Emisión AFIP sigue andando (cliente zeep cacheado)

---

## Acceptance Criteria
- [ ] Argon2 corre fuera del event loop; el test de no-bloqueo lo prueba
- [ ] Los 6 call sites usan `await`; los fakes de tests son async
- [ ] Pool dimensionado por env var, con defaults sanos y `pool_timeout` bajo
- [ ] Un solo `httpx.AsyncClient` por proceso, cerrado en el `lifespan`
- [ ] Credenciales por request: **no se comparten headers entre tenants**
- [ ] Cliente zeep de AFIP cacheado
- [ ] Suite completa verde, sin regresiones

## Completion Checklist
- [ ] Código en inglés; textos de usuario en español
- [ ] `domain` sigue sin importar frameworks
- [ ] `me.py`, `auth.py`, `.mcp.json` intactos
- [ ] Nada hardcodeado (todo por settings)
- [ ] Sin scope creep (bus, rate limiter y outbox son otras fases)

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| **Mezclar credenciales entre tenants** al compartir el cliente HTTP | Media | **Alto (seguridad)** | Headers por request, nunca en el constructor; test explícito con 2 tenants |
| Un `await` faltante deja una corrutina sin ejecutar | Media | Alto (login roto) | `ruff`/typing lo detectan; suite completa; validación manual del login |
| Fakes de tests sin migrar dan falsos positivos | Media | Medio | Revisar todos los dobles; la suite completa es el gate |
| Pool mal dimensionado agota `max_connections` de Postgres | Baja | Alto | Defaults conservadores (10+20); documentado; se revisa al sumar workers (Fase 3) |
| Cerrar el cliente HTTP con requests en vuelo | Baja | Bajo | Cierre en el `lifespan`, al apagar |
| El executor default se satura (compartido con AFIP) | Baja | Medio | Medir antes de agregar un pool dedicado |

## Notes

- **Por qué esta fase va antes de escalar horizontalmente**: sumar workers/réplicas con Argon2 bloqueando y el pool sin dimensionar multiplica el problema en vez de resolverlo. Primero cada proceso rinde bien, después se agregan procesos.
- **Lo que ya está bien y no se toca**: `AfipWsaa` cachea el ticket con `asyncio.Lock` (sin thundering herd); no hay `requests` ni `time.sleep` en toda la base; el DI usa `Singleton` para lo caro y `Factory` para lo liviano; ninguna llamada externa ocurre dentro de una transacción abierta.
- **Medición**: la mejora del hasheo se prueba con el test de no-bloqueo, no con latencia contra prod (la red a Railway domina el número y no sirve como señal).
