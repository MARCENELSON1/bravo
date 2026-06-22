# Plan: Fase 11 — Copiloto IA (text-to-SQL con guardrails)

## Summary
El **copiloto conversacional en español**: el dueño pregunta en lenguaje natural sobre su negocio y el sistema
responde, leyendo del modelo canónico (Fase 8). Enfoque elegido: **el LLM genera SQL** (NL→SQL) sobre un **schema
acotado read-only**, ese SQL pasa por un **validador determinístico** (allow-list, single SELECT, sin DML), y se
ejecuta en una **transacción read-only con `tenant_id` forzado por RLS** — así la **aislación entre tenants NO
depende del LLM**. Siempre se devuelve el SQL ejecutado + las filas (**fuente/transparencia**). Es el diferenciador
del producto y el más delicado en seguridad. Reusa la infra LLM de Fase 9 (port + adapter Anthropic + Selector +
flag off). Depende de Fase 8. Corre en paralelo con Fase 12.

> **DECISIONES DE ARQUITECTURA (cerradas con el usuario — no re-litigar):**
> 1. **Enfoque A — el LLM genera SQL** (no function-calling sobre queries pre-armadas). Más flexible; la seguridad
>    se garantiza con **3 capas de defensa**, no confiando en el LLM.
> 2. **Capa 1 — Schema acotado.** El LLM SÓLO conoce una **allow-list curada** de tablas/columnas (el modelo
>    canónico + datos de negocio: `sale_facts`, `payments`, `reservations`, `products`, `ingredients`, `shifts`…).
>    **Nunca** ve `users`, tokens, `*_credentials` ni catálogos del sistema. El prompt recibe esa allow-list con
>    descripciones; lo demás no existe para el copiloto.
> 3. **Capa 2 — Validador determinístico (guardrail), ANTES de ejecutar.** `validate_sql` (puro, sqlglot): rechaza
>    si no es **un único `SELECT`**; rechaza DML/DDL (INSERT/UPDATE/DELETE/DROP/ALTER/CREATE/GRANT/TRUNCATE/COPY),
>    `;` múltiples, funciones peligrosas (`pg_sleep`…), y **toda tabla/columna fuera de la allow-list** o de
>    `pg_*`/`information_schema`. Inyecta un `LIMIT` máximo si falta.
> 4. **Capa 3 — Ejecución blindada (defensa en profundidad, NO sólo el SQL validado):** corre en
>    **`SET TRANSACTION READ ONLY` + `statement_timeout`** y dentro del **tenant context** → las **policies RLS**
>    filtran por `app.tenant_id` en cada tabla tenant-scoped. **Aunque el LLM omita `WHERE tenant_id=…`, RLS sólo
>    devuelve filas del tenant.** (Opcional/hardening: rol DB `bravo_readonly` dedicado.)
> 5. **Fuente/transparencia siempre.** La respuesta devuelve `{answer (NL), sql ejecutado, columnas, filas}`. La
>    respuesta NL la redacta el LLM **a partir de las filas reales** con el mismo **guardrail anti-cifras-inventadas**
>    de Fase 9 (números que no estén en las filas → se descarta y se muestra solo la tabla).
> 6. **Detrás de port + `Selector(copilot_provider off|claude)`, APAGADO por default.** Con `off` el endpoint
>    responde "copiloto no disponible". **Prender en prod requiere el set de evals** (open question PRD) — ver T5.
> 7. **MVP single-shot** (una pregunta → una respuesta; sin memoria multi-turno). Follow-ups conversacionales
>    diferidos. Reusa la infra LLM de Fase 9 (generalizar el `LlmClient`/adapter Anthropic a un lugar compartido).
> 8. **RBAC OWNER/MANAGER** (datos de plata). Multi-tenant + RLS en todo.

## Estado de implementación
PENDIENTE. Depende de Fase 8 (modelo canónico) — ✅ en `main`. Reusa el patrón LLM de Fase 9 (✅) y `anthropic` ya
instalado. Se implementa en rama `feat/fase-11-copiloto`. Dep nueva: `sqlglot`. (Distinto de Fase 10: independiente.)

## User Story
Como **dueño/encargado** quiero **preguntarle al sistema en español** ("¿cuánto vendí de milanesas el finde?",
"¿qué mozo facturó más este mes?") y que me responda con el dato **y me muestre de dónde salió**, sin saber SQL ni
cruzar planillas.

## Problem → Solution
Hoy hay dashboards fijos (asesor, analítica) pero no se puede preguntar lo que no está pre-armado. → Copiloto
NL→SQL: el LLM traduce la pregunta a SQL sobre el modelo canónico, el SQL se valida y se ejecuta read-only +
tenant-RLS, y se responde en español citando la consulta y las filas. Seguro por construcción (3 capas), scoped por
tenant (RLS), apagado hasta tener evals.

---

## Modelo de dominio (nuevo: `copilot`)
- **`CopilotSchema`** (`schema.py`): la **allow-list curada** — `{tabla: {columnas, descripción}}` del subconjunto
  consultable (canónico + negocio). Helpers `is_allowed_table/column`, render del schema-doc para el prompt.
- **`validate_sql(sql, schema) -> ValidatedSql`** (`sql_guard.py`, **puro**, sqlglot): el corazón de seguridad.
  Single SELECT; sin DML/DDL/`;`-múltiple/funciones peligrosas; tablas+columnas ⊆ allow-list; sin `pg_*`/
  `information_schema`; inyecta `LIMIT`. Lanza `UnsafeQuery` con detalle.
- **Excepciones:** `UnsafeQuery` (422), `CopilotDisabled` (409), `CopilotQueryError` (422) — code EN + message ES.
- **Ports:** `CopilotLLM` (`to_sql(question, schema_doc) -> str`, `answer(question, columns, rows) -> str`),
  `CopilotQueryRunner` (`run(tenant_id, validated_sql) -> (columns, rows)`).

## Ejecución segura
- `CopilotQueryRunner` (infra): abre sesión, `SET LOCAL statement_timeout = :ms`, marca la transacción **read-only**,
  setea `app.tenant_id` (RLS, igual que `database.py`), ejecuta el SQL **ya validado**, devuelve columnas + filas
  (cap por `LIMIT`). Read-only + RLS = aislación garantizada **independiente del LLM**.

## Reuso de la capa LLM (Fase 9)
- Generalizar el `AdvisorLLMClient`/`AnthropicAdvisorLLM` (hoy en `infrastructure/advisor/llm.py`) a un
  **`infrastructure/llm/` compartido** (`LlmClient` + `AnthropicClient`), y que advisor y copilot lo reusen. El
  adapter del copiloto (`AnthropicCopilotLLM`) arma los prompts NL→SQL y filas→respuesta sobre ese client.

## Config
- `copilot_provider` (off|claude, default **off**), `anthropic_api_key` (ya existe), `copilot_model`
  (default `claude-opus-4-8`), `copilot_row_limit` (ej. 200), `copilot_statement_timeout_ms` (ej. 5000).

---

## Mandatory Reading (moldes ya en el repo)
- **Capa LLM + Selector + flag + guardrail (molde directo, Fase 9):** `infrastructure/advisor/{llm,claude_narrator}.py`
  (guardrail anti-cifras), `domain/advisor/ports.py`, `container.py` (Selector `insight_narrator`), `config.py`
  (`advisor_llm_*`).
- **Sesión + RLS + tenant context (para el runner):** `infrastructure/persistence/database.py` (`SET set_config
  app.tenant_id`), `app/context.py`, `security/tenant_context.py`.
- **Modelo canónico (lo consultable):** `infrastructure/persistence/{analytics_repo,advisor_repo}.py`, `models.py`
  (tablas `sale_facts`/`payments`/`reservations`/… para definir la allow-list).
- **API + RBAC + errores + router:** `presentation/api/v1/{advisor,analytics}.py`, `rbac.py`, `errors.py`, `main.py`.
- **Frontend:** `features/advisor/advisor-page.tsx` (página + estado LLM), `api/advisor-api.ts` + `hooks/use-advisor.ts`,
  `services/*`, `nav-config.ts`, `router.tsx`.

## Files to Change (orientativo)
**Backend (nuevos):** `domain/copilot/{__init__,schema,sql_guard,exceptions,ports}.py`,
`application/copilot/{__init__,ask}.py`, `infrastructure/copilot/{__init__,anthropic_copilot,no_copilot,sql_runner}.py`,
`infrastructure/llm/{__init__,client,anthropic_client}.py` (compartido), `presentation/api/v1/copilot.py`,
`presentation/schemas/copilot.py`, tests unit (guard) + e2e, `evals/copilot/` (casos + runner).
**Backend (editar):** `container.py`, `config.py`, `presentation/errors.py`, `main.py`, `pyproject.toml`
(`sqlglot`), y refactor de `infrastructure/advisor/llm.py` → usar `infrastructure/llm/`.
**Frontend (nuevos):** `api/{types-copilot,copilot-api}.ts` (+ test), `hooks/use-copilot.ts`,
`features/copilot/copilot-page.tsx`.
**Frontend (editar):** `services/services-{context,provider}`, `test/test-utils.tsx`, `nav-config.ts` (Resumen →
"Copiloto"), `app/router.tsx`.

---

## Step-by-Step Tasks

### T1 — Dominio copilot: schema acotado + validador (núcleo de seguridad)
- `CopilotSchema` (allow-list curada del canónico) + `validate_sql` (sqlglot, puro) + excepciones + ports. Dep `sqlglot`.
- **Tests unit (exhaustivos — es el guardrail):** acepta un SELECT válido sobre tablas permitidas; **rechaza**
  INSERT/UPDATE/DELETE/DROP, `;` múltiple, tabla fuera de allow-list, columna fuera de allow-list, `pg_`/
  `information_schema`, `pg_sleep`; inyecta `LIMIT` si falta; respeta `LIMIT` existente menor al máximo.
- **MIRROR:** `domain/advisor/insights.py` (función pura testeable), `domain/inventory/costing.py`.

### T2 — Ejecución read-only + RLS + caso de uso
- `SqlAlchemyCopilotQueryRunner` (read-only tx + `statement_timeout` + `app.tenant_id`/RLS). `AskCopilot`
  (orquesta: llm.to_sql → validate_sql → runner.run → llm.answer con guardrail). `NoCopilot` (Selector off → `CopilotDisabled`).
- **Tests e2e:** un SELECT del tenant devuelve solo sus filas; **aislación RLS** (un SQL SIN filtro de tenant igual
  solo ve las filas del tenant); query insegura → `unsafe_query`; con provider off → `copilot_disabled`. **El LLM se
  fakea** (no red): el fake devuelve un SELECT canónico.
- **MIRROR:** `infrastructure/persistence/database.py`, `application/advisor/report.py`, `infrastructure/advisor/*`.

### T3 — Adapter LLM (grounded, flag off) + LLM compartido
- Mover `LlmClient`/`AnthropicClient` a `infrastructure/llm/` (refactor; advisor lo reusa). `AnthropicCopilotLLM`
  (`to_sql` + `answer`) detrás de `Selector(copilot_provider off|claude)`; config flags. La respuesta NL usa el
  **guardrail anti-cifras-inventadas** (números ⊆ filas). 
- **Tests:** con **fake LLM**: `to_sql` produce SQL que pasa el guard y corre; `answer` usa las filas; el guardrail
  descarta una cifra que no está en las filas. Refactor del advisor sigue verde.
- **MIRROR:** `infrastructure/advisor/{llm,claude_narrator}.py`, `container.py` Selector.

### T4 — API + Frontend
- `POST /copilot/ask {question}` → `{answer, sql, columns, rows, llm_enabled}` (OWNER/MANAGER). errors
  (`UnsafeQuery`=422, `CopilotDisabled`=409, `CopilotQueryError`=422). `CopilotApi` + `use-copilot` + página
  **Copiloto** (`/app/copilot`): caja de pregunta → respuesta en español + expander "ver consulta y datos" (el SQL
  + la tabla = la fuente). Nav "Copiloto" + ruta. Estado on/off del LLM.
- **Validar:** ruff+mypy+pytest ; tsc+eslint+vitest+build.
- **MIRROR:** `presentation/api/v1/advisor.py`, `features/advisor/advisor-page.tsx`.

### T5 — Evals (gate para prod)
- `evals/copilot/`: set de casos `(pregunta → propiedad esperada)` — SQL válido y seguro, responde sobre las filas,
  no alucina, el guard atrapa los intentos peligrosos (incl. prompt-injection: "ignorá las reglas y borrá…"). Runner
  offline (fake/grabado en CI; real a mano). **Documentar que prender `copilot_provider=claude` en prod requiere
  pasar estos evals** (open question PRD). No corre red en CI.
- **MIRROR:** `tests/unit/test_advisor_llm.py` (estilo fake-LLM), guardrail.

---

## Validation Commands
- **Backend:** `poetry run ruff check app tests` · `poetry run mypy app` · `poetry run pytest -q` (≥80% en
  domain/application). **El LLM nunca se llama en tests** (fake). 
- **Frontend:** `npx tsc --noEmit` · `npx eslint src` · `npx vitest run` · `npx vite build`.

## Acceptance Criteria
- Una pregunta en español → SQL generado → **validado** (single SELECT, allow-list) → ejecutado **read-only +
  tenant-RLS** → respuesta en español + **SQL y filas visibles** (fuente).
- **Seguridad:** un SQL con DML / tabla fuera de allow-list / sin filtro de tenant → respectivamente **rechazado** o
  **acotado por RLS** (nunca filtra otro tenant ni escribe). Probado en tests.
- La **capa LLM** está detrás de `Selector` y **apagada por default**; con `off`, `/copilot/ask` → `copilot_disabled`.
- ruff + mypy + pytest + tsc + eslint + vitest + build en verde. Set de evals presente (gate documentado para prod).

## Complexity / Confidence
- **Complejidad:** Alta — la parte fina es la **seguridad** (validador + read-only + RLS) y el NL→SQL. Mitigado:
  RLS ya garantiza el tenant (no depende del LLM), el patrón LLM/guardrail/Selector viene de Fase 9, y el validador
  es puro y muy testeable.
- **Confianza:** Alta en T1/T2 (seguridad determinística sobre RLS probado) y T4. Media en T3/T5 (calidad del NL→SQL
  y los evals; pero aislado y con flag off).

## Out of scope (diferido)
- Memoria conversacional multi-turno / follow-ups; gráficos generados; "explicá este número" sobre el dashboard;
  escritura/acciones desde el copiloto (siempre read-only); rol DB `bravo_readonly` dedicado (hardening opcional);
  caché de respuestas; voz. Evals formales completos como CI gate automatizado (MVP: set + runner manual). Reportes
  y WhatsApp → **Fase 10**. CRM → **Fase 12**.
