# Plan: Escalabilidad Fase 4 — sacar el trabajo diferible del camino crítico

## Summary

Cuando la cocina marca un plato listo, el request espera a que se manden los push (query de tokens → OAuth con Google → un POST a FCM **por cada dispositivo, secuencial**) antes de responder. Cuando se cobra, espera además a que se consuma el stock y se proyecten las ventas. Nada de eso necesita bloquear al usuario. Esta fase lo mueve a un **outbox** —el patrón que el proyecto ya usa para impuestos— y, de paso, resuelve algo que faltaba: **nadie drena el outbox existente**.

## User Story

Como **cocinero marcando un plato listo** (o **cajero cobrando**), quiero **que la app responda al instante**, para **no esperar a que terminen tareas que no me importan en ese momento**.

## Problem → Solution

**Hoy:** `_notify_order_ready` (`order/use_cases.py:626`) y `_notify_assigned` (`payment/use_cases.py:484`) hacen `await` sobre FCM; `_fire_sale_effects` (`payment/use_cases.py:81,460`) consume stock y proyecta ventas dentro del request de cobro. Y el `TaxReportLedger` encola impuestos que **nadie procesa**: no existe worker, scheduler ni script de drain.

**Después:** esas tareas se encolan en una tabla (transaccional, con reintento) y un **drainer** las procesa fuera del request. El usuario ve la respuesta inmediata; el trabajo ocurre igual, con reintentos si falla.

## Metadata

- **Complexity**: Medium-Large
- **Source PRD**: `.claude/PRPs/prds/escalabilidad-backend.prd.md`
- **PRD Phase**: Fase 4 — Outbox del camino crítico
- **Estimated Files**: ~14 (1 port, 1 tabla + migración, 1 drainer, 2 handlers, casos de uso, container, main, tests)
- **Depends on**: Fases 1-3 (`e50a87c`, `2874a86`, `a41902c`)

---

## UX Design

**Internal change — no user-facing UX transformation.** El usuario percibe que "marcar listo" y "cobrar" responden más rápido; los push y los efectos ocurren igual.

### Interaction Changes

| Touchpoint | Before | After | Notes |
|---|---|---|---|
| Cocina marca un curso listo | Espera tokens + OAuth + N POSTs a FCM | Responde al instante | El push llega igual, en ~1s |
| Cajero cobra | Espera stock + proyección (+ push si aplica) | Responde al instante | Los efectos se aplican igual |
| Push que falla (device apagado) | Se traga en silencio, se pierde | Reintento con backoff | Mejor que hoy |
| Impuestos encolados | **Nunca se enviaban** (sin drainer) | Se procesan | Bug latente que esta fase cierra |

---

## Mandatory Reading

| Priority | File | Lines | Why |
|---|---|---|---|
| P0 | `app/application/tax/reporting.py` | 60-80 | **El patrón outbox de la casa**: `enqueue` idempotente / `list_pending` / `mark_sent` |
| P0 | `app/infrastructure/persistence/tax_report_repo.py` | todo | Su implementación: cómo modela reintentos y estado |
| P0 | `app/application/payment/use_cases.py` | 46-90, 440-490 | `_settle_order` y `_fire_sale_effects`: lo que hay que diferir |
| P0 | `app/application/order/use_cases.py` | 419-440, 620-630 | `_notify_order_ready` y su llamada desde `AdvanceItem` |
| P0 | `app/infrastructure/notification/fcm_service.py` | 55-75 | Lo que cuesta un push: tokens + OAuth + POST por device |
| P1 | `app/infrastructure/persistence/models.py` | — | Patrón de tabla tenant-scoped con RLS (mirar `tax_reports`) |
| P1 | `alembic/versions/0055_hot_path_indexes.py` | todo | Formato de migración; head actual |
| P1 | `app/main.py` | — | `lifespan` (ahí se engancha el drainer) |
| P2 | `app/infrastructure/http/client.py` | todo | Recurso de proceso con `aclose()` (Fase 2) — patrón para el drainer |
| P2 | `app/container.py` | — | Wiring; `Singleton` vs `Factory` |

## External Documentation

| Topic | Source | Key Takeaway |
|---|---|---|
| Transactional outbox | patrón | Escribir el "pendiente" en la **misma transacción** que el cambio de negocio: si commitea el cobro, commitea la tarea |
| `SELECT ... FOR UPDATE SKIP LOCKED` | Postgres | Permite que varios drainers tomen filas distintas sin pisarse — necesario con N réplicas (Fase 3) |
| Backoff exponencial | patrón | Reintentos espaciados; tope de intentos para no reintentar para siempre |

---

## Patterns to Mirror

### OUTBOX_PORT (el que ya existe)
```python
# SOURCE: app/application/tax/reporting.py:65-77
class TaxReportLedger(ABC):
    """Durable outbox of taxable sales to report. Tenant-scoped."""
    async def enqueue(self, tenant_id: str, order_id: str) -> None:
        """Mark an order as needing a tax report. Idempotent per (tenant, order)."""
    async def list_pending(self, tenant_id: str, *, limit: int = 100) -> list[PendingTaxReport]: ...
    async def mark_sent(self, report_id: str, external_id: str) -> None: ...
```

### FAIL_OPEN_SIDE_EFFECT (Fases 1 y 3)
```python
# SOURCE: app/infrastructure/realtime/redis_bus.py:71-80
# Todo, incluido obtener el cliente, va DENTRO del try: la promesa de que un
# efecto secundario roto no rompe el request no puede depender de que el
# provider nunca lance.
```

### PROCESS_RESOURCE_LIFESPAN (Fase 2)
```python
# SOURCE: app/infrastructure/http/client.py + app/main.py
# Recurso de proceso como Singleton, arrancado/cerrado una vez en el lifespan.
```

---

## Files to Change

| File | Action | Justification |
|---|---|---|
| `app/application/outbox/ports.py` | CREATE | `OutboxPort` genérico: `enqueue(kind, tenant_id, payload)` / `claim_batch` / `mark_done` / `mark_failed` |
| `app/infrastructure/persistence/outbox_repo.py` | CREATE | Implementación con `FOR UPDATE SKIP LOCKED`, intentos y `next_attempt_at` |
| `alembic/versions/0056_outbox.py` | CREATE | Tabla `outbox_tasks` (tenant-scoped, RLS, índice por estado+`next_attempt_at`) |
| `app/infrastructure/persistence/models.py` | UPDATE | `OutboxTaskORM` |
| `app/application/outbox/drainer.py` | CREATE | Loop que reclama lote, despacha por `kind`, marca resultado, backoff |
| `app/application/outbox/handlers.py` | CREATE | Handlers: `push_notification`, `sale_effects`, `tax_report` |
| `app/application/order/use_cases.py` | UPDATE | `_notify_order_ready` encola en vez de `await` a FCM |
| `app/application/payment/use_cases.py` | UPDATE | `_notify_assigned` y `_fire_sale_effects` encolan |
| `app/container.py` | UPDATE | Wiring del outbox, handlers y drainer |
| `app/main.py` | UPDATE | Arrancar/parar el drainer en el `lifespan` |
| `app/config.py` | UPDATE | `OUTBOX_DRAIN_ENABLED` (default **true**), intervalo, tamaño de lote, máx. intentos |
| `app/scripts/drain_outbox.py` | CREATE | Drain manual (operación y debugging) |
| `tests/unit/test_outbox*.py` | CREATE | Contrato, reintentos, idempotencia, `SKIP_LOCKED` |
| `tests/integration/test_e2e_outbox.py` | CREATE | Cobro/marcar-listo encolan y el drenado los aplica |

## NOT Building

- **No se toca el `EventBus`** — el SSE debe seguir siendo inmediato: es lo que hace sentir la app en vivo. Solo se difiere el **push a FCM** (que ya es asincrónico por naturaleza).
- **No se difiere nada que el usuario necesite ver al instante**: el estado de la orden, el pago registrado y el total se siguen escribiendo dentro del request.
- **No se agrega Celery/RQ ni un broker** — la tabla + drainer alcanza y es transaccional con el negocio (decisión ya registrada en el PRD).
- **No se difiere la emisión AFIP** del endpoint de facturar: el cajero necesita el CAE en pantalla. (El `tax_report` del outbox es otra cosa: el reporte al proveedor fiscal.)
- **No se pagina `GET /orders`** — Fase 5.
- **No se cambia el `CMD` del Dockerfile** ni se prenden réplicas.

---

## Step-by-Step Tasks

### Task 1: `OutboxPort` + tabla
- **ACTION**: Un outbox genérico por `kind`, reusable para los tres casos.
- **IMPLEMENT**: Port con `enqueue(kind, tenant_id, payload, dedup_key=None)`, `claim_batch(limit)`, `mark_done(id)`, `mark_failed(id, error)`. Tabla `outbox_tasks`: `id`, `tenant_id`, `kind`, `payload` (JSONB), `status` (`pending|done|failed`), `attempts`, `next_attempt_at`, `last_error`, `dedup_key`, timestamps. Índice por `(status, next_attempt_at)` y único parcial por `(tenant_id, kind, dedup_key)` cuando `dedup_key` no es null.
- **MIRROR**: `OUTBOX_PORT` + patrón de tabla tenant-scoped con RLS (`tax_reports`).
- **GOTCHA**: **RLS** — el drainer corre sin request, así que necesita poder leer de todos los tenants: definir explícitamente cómo (rol con bypass o `SET LOCAL` por fila). No dejarlo implícito.
- **VALIDATE**: `poetry run alembic upgrade head` + `poetry run pytest tests/unit -k outbox -q`.

### Task 2: Encolar dentro de la transacción
- **ACTION**: Que la tarea se persista atómicamente con el cambio que la origina.
- **IMPLEMENT**: `enqueue` participa de la misma sesión/transacción que la escritura de negocio (si el cobro no commitea, la tarea tampoco existe).
- **GOTCHA**: El proyecto usa **"sesión por llamada de repo"**, así que esto **no es gratis**: hay que decidir cómo compartir la sesión, o aceptar explícitamente que el enqueue va en su propia transacción inmediatamente después (y documentar la ventana de riesgo: si el proceso muere entre ambas, la tarea se pierde). **Elegí una y justificala**; si vas por la segunda, dejá claro que es una desviación consciente del patrón outbox puro.
- **VALIDATE**: Test que verifica que un cobro fallido no deja tareas huérfanas.

### Task 3: Drainer con backoff
- **ACTION**: El proceso que ejecuta las tareas.
- **IMPLEMENT**: Loop async que cada N segundos reclama un lote (`FOR UPDATE SKIP LOCKED`), despacha por `kind`, y marca `done`/`failed` con `attempts++` y `next_attempt_at` exponencial. Tope de intentos ⇒ `failed` definitivo y log de error.
- **MIRROR**: `PROCESS_RESOURCE_LIFESPAN`.
- **GOTCHA**: `SKIP_LOCKED` es lo que permite que **varias réplicas** (Fase 3) drenen sin pisarse. Sin eso, N réplicas mandarían el mismo push N veces. El drainer **nunca** debe tumbar el proceso: cualquier excepción de un handler se captura y marca la fila, no propaga.
- **VALIDATE**: Test de reintento con backoff y de tope de intentos.

### Task 4: Handler de push
- **ACTION**: Mover FCM fuera del request.
- **IMPLEMENT**: `_notify_order_ready` y `_notify_assigned` pasan a `enqueue("push_notification", ...)` con el payload ya resuelto (título, cuerpo, `user_id`, data). El handler llama a `NotificationService`.
- **GOTCHA**: El payload debe llevar **todo lo necesario ya calculado** (nombre de mesa, ítems del curso): si el handler recalcula leyendo la orden, puede encontrarla cambiada y mandar un push desactualizado. **Snapshot, no referencia.**
- **VALIDATE**: Test de que marcar listo encola y no llama a FCM; y de que el drenado sí lo llama.

### Task 5: Handler de efectos de venta
- **ACTION**: Sacar stock y proyección del cobro.
- **IMPLEMENT**: `_fire_sale_effects` encola `sale_effects`; el handler ejecuta consumo de stock + proyección + `tax_outbox`.
- **GOTCHA**: **Idempotencia obligatoria** — un reintento no puede descontar el stock dos veces. Ya existe `exists_for_order` en el consumo; verificar que la proyección también sea idempotente por orden. Sin esto, un reintento corrompe el inventario.
- **VALIDATE**: Test que drena dos veces la misma tarea y verifica que el stock se descontó **una** vez.

### Task 6: Drenar el `tax_outbox` existente
- **ACTION**: Cerrar el bug latente: hoy se encola y nadie procesa.
- **IMPLEMENT**: `kind = "tax_report"` que toma los pendientes del `TaxReportLedger` y los envía por el reporter configurado.
- **GOTCHA**: ~~Puede haber filas viejas acumuladas~~ **VERIFICADO EN PROD (2026-09-05): `{pending:0, failed:0, sent:0}` y TaxJar `connected:false`** (es para el mercado US, aún inactivo). No hay avalancha posible: el riesgo está descartado. Aun así, el handler no debe asumir que hay un reporter configurado — si no lo hay, la tarea se marca `done` (nada que reportar) en vez de fallar en loop.
- **VALIDATE**: Ya contado (0 pendientes). Test de que sin reporter configurado no entra en bucle de reintentos.

### Task 7: Wiring, lifespan y script
- **ACTION**: Arrancar el drainer con la app y poder correrlo a mano.
- **IMPLEMENT**: `Singleton` en el container; `asyncio.create_task` en el `lifespan` con cancelación limpia al apagar. `OUTBOX_DRAIN_ENABLED` (default **true**). `app/scripts/drain_outbox.py` para operar/debuggear.
- **GOTCHA**: Al apagar, cancelar la tarea y **esperar** a que termine el lote en curso (si no, quedan filas reclamadas y sin procesar hasta que expire el lock).
- **VALIDATE**: Arrancar y apagar la app sin tareas colgadas ni warnings de asyncio.

---

## Testing Strategy

### Unit Tests

| Test | Input | Expected Output | Edge Case? |
|---|---|---|---|
| `enqueue` idempotente por `dedup_key` | 2 enqueues iguales | 1 fila | ✅ |
| `claim_batch` no entrega la misma fila 2 veces | 2 drainers | Filas disjuntas | ✅ **el motivo de SKIP_LOCKED** |
| Reintento con backoff | Handler que falla | `attempts++`, `next_attempt_at` futuro | ✅ |
| Tope de intentos | Falla N+1 veces | `failed`, deja de reintentar | ✅ |
| Handler que lanza no tumba el drainer | Excepción | Se marca la fila, el loop sigue | ✅ |
| Push encolado, no enviado in-line | Marcar listo | FCM **no** llamado; hay 1 tarea | ✅ **el motivo** |
| Efectos de venta idempotentes | Drenar 2× | Stock descontado 1 vez | ✅ **corrupción de datos** |
| Payload es snapshot | Orden cambia tras encolar | El push refleja el momento del encolado | ✅ |

### Edge Cases Checklist
- [ ] Proceso muere entre el negocio y el enqueue (documentar ventana según Task 2)
- [ ] Proceso muere con un lote reclamado (¿se libera? ¿lock expira?)
- [ ] Dos réplicas drenando simultáneo
- [ ] Payload no serializable
- [ ] Tenant borrado con tareas pendientes
- [ ] Cola grande al prender por primera vez (Task 6)

---

## Validation Commands

### Static Analysis
```bash
cd backend && poetry run ruff check app tests
```
EXPECT: sin errores **nuevos** (preexistentes: `me.py` I001, `test_e2e_finance.py` E501 ×2 — no tocar)

### Full Test Suite
```bash
cd backend && poetry run pytest -q -p no:warnings
```
EXPECT: exit 0 (baseline: **809** tests)

### Database Validation
```bash
cd backend && poetry run alembic upgrade head && poetry run alembic current
```
EXPECT: `0056_outbox`

### Manual Validation
- [ ] Marcar un curso listo responde sin esperar a FCM, y el push llega igual
- [ ] Un cobro responde sin esperar stock/proyección, y los efectos se aplican
- [ ] Apagar la app no deja tareas reclamadas colgadas
- [ ] **Contar `tax_reports` pendientes en prod antes de habilitar el drainer**

---

## Acceptance Criteria
- [ ] Marcar listo y cobrar no esperan trabajo diferible
- [ ] Las tareas se aplican igual, con reintento y tope
- [ ] Idempotencia probada: drenar dos veces no duplica efectos
- [ ] `SKIP_LOCKED`: dos drainers no procesan la misma fila
- [ ] El drainer nunca tumba el proceso
- [ ] El `tax_outbox` existente por fin se procesa (con el volumen acumulado revisado)
- [ ] Suite completa verde

## Completion Checklist
- [ ] Código en inglés; `domain` sin frameworks
- [ ] `me.py`, `auth.py`, `.mcp.json`, `Dockerfile` intactos
- [ ] Sin scope creep (la paginación es Fase 5)
- [ ] Decisión de Task 2 (transaccionalidad) documentada explícitamente

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| **Reintento duplica efectos de venta** (stock descontado 2×) | Media | **Alto (datos)** | Idempotencia por orden + test de doble drenado |
| Enqueue fuera de transacción pierde tareas si el proceso muere | Media | Medio | Decisión explícita en Task 2 y ventana documentada |
| Dos réplicas mandan el mismo push | Media | Medio | `FOR UPDATE SKIP LOCKED` + test |
| ~~Avalancha de tax reports viejos~~ **DESCARTADO** | — | — | Verificado en prod: 0 pendientes, TaxJar no conectado |
| Push desactualizado si el handler recalcula | Media | Bajo | Payload como snapshot |
| El drainer muere en silencio y nadie lo nota | Media | Medio | Log al arrancar/parar; el script manual como fallback |
| RLS bloquea al drainer (corre sin request) | Media | Alto | Resolverlo explícito en Task 1 |

## Notes

- **Esta fase mejora latencia percibida, no capacidad**: el trabajo se hace igual, pero fuera del camino del usuario. La capacidad la dieron las Fases 1-3.
- **El hallazgo que motiva parte de la fase**: el `TaxReportLedger` existe y encola, pero **no hay ningún consumidor** en el código — ni worker, ni scheduler, ni script. Lo verifiqué buscando `list_pending`/`mark_sent` fuera del repo: no hay callers. Es un bug latente que esta fase cierra.
- **Por qué el push sí y el SSE no**: el SSE es lo que hace que la app se sienta viva y ya es liviano (publicar a un canal). El push es lento por naturaleza (OAuth + N POSTs) y su entrega nunca fue inmediata.
