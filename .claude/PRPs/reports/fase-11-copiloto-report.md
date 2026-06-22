# Implementation Report: Fase 11 — Copiloto IA (text-to-SQL con guardrails)

## Summary
Copiloto conversacional en español: pregunta en NL → el LLM genera SQL → **validador determinístico** (allow-list,
single SELECT, sin DML) → ejecución **read-only + tenant forzado por RLS** → respuesta en español **grounded** +
la consulta y las filas como **fuente**. La aislación entre tenants la garantiza **RLS, no el LLM**. Detrás de
`Selector(copilot_provider off|claude)`, **apagado por default**; prender exige el set de evals. Reusa la infra LLM
de Fase 9. Independiente de Fase 10.

## Assessment vs Reality

| Metric | Predicted (Plan) | Actual |
|---|---|---|
| Complexity | Alta (seguridad + NL→SQL) | Coincide; el validador sqlglot salió a la primera |
| Confidence | Alta T1/T2/T4, Media T3/T5 | Confirmado; seguridad determinística sobre RLS probado |
| Files Changed | ~30 nuevos/editados | 36 archivos (1223+ líneas) |

## Tasks Completed

| # | Task | Status | Notes |
|---|---|---|---|
| T1 | Dominio: schema acotado + validador SQL | ✅ Complete | sqlglot, 14 tests; núcleo de seguridad |
| T2 | Runner read-only/RLS + AskCopilot | ✅ Complete | transaction_read_only + statement_timeout + RLS |
| T3 | Adapter LLM (flag off) + cliente compartido | ✅ Complete | AnthropicCopilotLLM + guardrail; 6 tests fake-LLM |
| T4 | API + Frontend | ✅ Complete | POST /copilot/ask + página Copiloto; 5 e2e + 1 front |
| T5 | Evals (gate de prod) | ✅ Complete | 25 evals adversariales (CI, sin LLM) + README del gate |

## Validation Results

| Level | Status | Notes |
|---|---|---|
| Static Analysis | ✅ Pass | ruff + mypy (252) limpios; tsc + eslint limpios |
| Unit Tests | ✅ Pass | 14 validador + 6 LLM (fake) + 25 evals adversariales + 1 lib front |
| Build | ✅ Pass | vite build ok |
| Integration (e2e) | ✅ Pass | 5 e2e: rows del tenant, **RLS aísla sin filtro de tenant**, unsafe rechazado, off-allowlist rechazado, disabled |
| Edge Cases | ✅ Pass | star, stacked, UNION a tabla prohibida, pg_*/info_schema, pg_read_file, prompt-injection |
| Coverage | ✅ Pass | copilot dominio+aplicación 98% |

## Files Changed (36)
**Backend nuevos:** `domain/copilot/{__init__,schema,sql_guard,exceptions,ports}.py`,
`application/copilot/{__init__,ask}.py`,
`infrastructure/copilot/{__init__,sql_runner,anthropic_copilot,no_copilot}.py`,
`infrastructure/llm/{__init__,client}.py` (cliente LLM compartido), `presentation/api/v1/copilot.py`,
`presentation/schemas/copilot.py`, `tests/unit/{test_copilot_sql_guard,test_copilot_llm,test_copilot_evals}.py`,
`tests/integration/test_e2e_copilot.py`, `evals/copilot/README.md`.
**Backend editados:** `container.py`, `config.py`, `presentation/errors.py`, `main.py`, `pyproject.toml`/`poetry.lock`
(`sqlglot`).
**Frontend nuevos:** `api/{types-copilot,copilot-api,copilot-api.test}.ts`, `hooks/use-copilot.ts`,
`features/copilot/copilot-page.tsx`.
**Frontend editados:** `services/services-{context,provider}.tsx`, `test/test-utils.tsx`, `nav-config.ts`,
`app/router.tsx`.

## Seguridad (cómo queda garantizada)
1. **Schema acotado** — el LLM sólo conoce 10 tablas de negocio; nunca `users`/tokens/credenciales; columnas
   sensibles/PII excluidas (`external_ref`, `customer_phone`, `password_hash`).
2. **Validador** — un único SELECT, sin DML/DDL/`;`-múltiple/`SELECT *`, tablas+columnas ⊆ allow-list, sin
   `pg_*`/`information_schema`, sin funciones peligrosas; inyecta `LIMIT`.
3. **Ejecución** — `transaction_read_only=on` + `statement_timeout` + `app.tenant_id` (RLS). **Verificado: las 10
   tablas de la allow-list tienen RLS**, así que aunque el SQL no filtre por tenant, sólo se ven las filas del
   tenant (test e2e explícito). La aislación NO depende del LLM.
4. **Respuesta** — grounded; guardrail descarta cifras que no estén en las filas; sin filas → fallback determinístico.

## Deviations from Plan
1. **Cliente LLM compartido nuevo** (`infrastructure/llm/client.py`) usado por el copiloto; el del asesor (Fase 9)
   se dejó **intacto** para no arriesgar Fase 9 bajo presión de costo (hay dos wrappers Anthropic; consolidar =
   cleanup diferido).
2. **T4 backend (API) se hizo junto con T2/T3** (el e2e con RLS lo necesitaba); commits agrupados.
3. **Evals (T5)** = set adversarial determinístico en CI + README del proceso de calidad manual (no un harness
   automatizado con LLM en CI — eso quedó fuera de alcance, como anota el plan).

## Issues Encountered
- **`SET LOCAL` no acepta binds** → el runner usa `set_config('statement_timeout'/'transaction_read_only', …, true)`
  (mismo patrón que `database.py` para `app.tenant_id`).
- **Respuesta con resultado vacío**: el guardrail (sólo numérico) aceptaba texto sin cifras → se fuerza fallback
  determinístico cuando no hay filas (no se confía en el LLM ahí).
- **Separadores de miles** ("$300.000" vs "300000"): el guardrail normaliza separadores antes de comparar números.

## Tests Written

| Test File | Tests | Coverage |
|---|---|---|
| `tests/unit/test_copilot_sql_guard.py` | 14 | validador (acepta/rechaza, LIMIT) |
| `tests/unit/test_copilot_evals.py` | 25 | SQL adversarial (21 rechazados) + benignos |
| `tests/unit/test_copilot_llm.py` | 6 | fences + guardrail anti-cifras (fake LLM) |
| `tests/integration/test_e2e_copilot.py` | 5 | rows del tenant, RLS, unsafe, off-allowlist, disabled |
| `frontend/src/api/copilot-api.test.ts` | 1 | cliente ask |

## Next Steps
- [ ] Code review via `/code-review`
- [ ] Merge a `main` (rama `feat/fase-11-copiloto`)
- [ ] **Antes de prender `copilot_provider=claude` en prod:** correr los evals (CI + calidad manual, ver
  `evals/copilot/README.md`); setear `COPILOT_PROVIDER=claude` (la `ANTHROPIC_API_KEY` ya está). **Caché pendiente**
  (2 llamadas LLM por pregunta).
- [ ] Fases restantes: **10** (Reportes+WhatsApp, trabada por elegir proveedor) y **12** (CRM).
