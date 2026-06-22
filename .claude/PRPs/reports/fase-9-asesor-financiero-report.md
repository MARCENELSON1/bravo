# Implementation Report: Fase 9 — Asesor financiero + Dashboard

## Summary
La Capa 2 arrancó: sobre el modelo canónico (Fase 8) se montó el **asesor financiero que habla en pesos** —
KPIs avanzados (food/labor/prime cost, **margen neto**, **punto de equilibrio**, mermas) + **insights proactivos**
agrupados en *Actuá hoy / Esta semana / Lo que viene / Bien hecho* + dashboard. Arquitectura en **dos capas**: un
**piso determinístico** (fuente de verdad, siempre corre, testeable) y una **capa LLM grounded** (Claude narra/
sintetiza sobre los números ya calculados, detrás de `Selector`, **apagada por default**, con guardrail
anti-cifras-inventadas). Prioridad PRD: diferenciador. Depende de Fase 8.

## Assessment vs Reality

| Metric | Predicted (Plan) | Actual |
|---|---|---|
| Complexity | Alta (fase más grande) | Coincide — KPIs + insights + LLM + dashboard |
| Confidence | Alta T1–T3/T5, Media T4 | Confirmado; T4 (LLM) salió aislado y con fake en tests |
| Files Changed | ~30 nuevos/editados | 44 archivos (2165+ líneas) |

## Tasks Completed

| # | Task | Status | Notes |
|---|---|---|---|
| T1 | Dominio advisor (KPIs + insights) + settings | ✅ Complete | kpis.py + detect_insights + AdvisorSettings; migración 0011; 15 unit |
| T2 | Read model + reporte determinístico | ✅ Complete | AdvisorReadModel + GetAdvisorReport + TemplateNarrator/NoSynthesis |
| T3 | API + RBAC | ✅ Complete | /advisor/report + /advisor/settings; 4 e2e |
| T4 | Capa LLM grounded (flag off) | ✅ Complete | ClaudeNarrator/Synthesizer + guardrail; 5 unit con fake LLM |
| T5 | Frontend dashboard | ✅ Complete | KPIs + insights por bucket + costos; 6 tests |

## Validation Results

| Level | Status | Notes |
|---|---|---|
| Static Analysis | ✅ Pass | ruff + mypy (237 archivos) limpios; tsc + eslint limpios |
| Unit Tests | ✅ Pass | 15 dominio (KPIs/insights/settings) + 5 LLM (guardrail) + 3 lib frontend |
| Build | ✅ Pass | `vite build` ok (warning de chunk preexistente) |
| Integration (e2e) | ✅ Pass | 4 e2e backend + 3 api frontend |
| Edge Cases | ✅ Pass | degradación sin costos, pérdida detectada, guardrail descarta alucinación, RLS |
| Coverage | ✅ Pass | advisor dominio+aplicación 99% (≥80% requerido) |

## Files Changed (44)
**Backend nuevos:** `domain/advisor/{__init__,value_objects,exceptions,kpis,insights,entities,repository,ports}.py`,
`application/advisor/{__init__,report,use_cases}.py`,
`infrastructure/advisor/{__init__,template_narrator,no_synthesis,llm,claude_narrator,claude_synthesizer}.py`,
`infrastructure/persistence/{advisor_settings_repo,advisor_repo}.py`, `presentation/api/v1/advisor.py`,
`presentation/schemas/advisor.py`, `alembic/versions/0011_advisor_settings.py`,
`tests/unit/{test_advisor,test_advisor_llm}.py`, `tests/integration/test_e2e_advisor.py`.
**Backend editados:** `models.py`, `mappers.py`, `container.py`, `config.py`, `presentation/errors.py`, `main.py`,
`tests/integration/conftest.py`.
**Frontend nuevos:** `api/{types-advisor,advisor-api,advisor-api.test}.ts`, `hooks/use-advisor.ts`,
`lib/{advisor,advisor.test}.ts`, `features/advisor/advisor-page.tsx`.
**Frontend editados:** `services/services-{context,provider}.tsx`, `test/test-utils.tsx`, `nav-config.ts`,
`app/router.tsx`.

## Deviations from Plan
1. **Dep `anthropic` NO agregada a `pyproject`** — se importa **lazy** dentro de `AnthropicAdvisorLLM` (sólo se
   necesita al prender `advisor_llm_provider=claude`, que está off). Evita churn de lock/instalación; en prod se
   agrega al habilitar el flag (con evals). Tests usan un **fake LLM** (nunca red).
2. **Settings sheet inline** en `advisor-page.tsx` (el plan listaba `advisor-settings-sheet.tsx` aparte) —
   componente interno no exportado, mismo patrón que el editor de receta.
3. **Onboarding por rubro: diferido** (estaba marcado opcional en T5). Los targets se editan en el sheet de costos.
4. `labor_cost` sale del **setting mensual prorrateado** (no de tarifas por hora, que no capturamos) — decisión ya
   anotada en el plan.

## Issues Encountered
- **Walrus inválido** en una regla de `detect_insights` (precedencia de `:=` con `and`) → reescrito sin walrus.
- **Proración no determinística por fecha** en los e2e → las aserciones con costos asertan estructura (labor>0,
  net<0, `losing_money` presente) en vez de montos exactos; el período default (mes corriente) siempre incluye la
  comanda recién pagada.
- **Segundo hook post-PAID**: el settle ya tenía el InventoryConsumer; el `SalesProjector` de Fase 8 sirvió de
  molde — acá no se tocó pagos (el asesor sólo lee).

## Tests Written

| Test File | Tests | Coverage |
|---|---|---|
| `tests/unit/test_advisor.py` | 15 | KPIs puros, break-even, settings, cada regla de insight |
| `tests/unit/test_advisor_llm.py` | 5 | guardrail: usa LLM grounded, descarta cifra inventada, fallback ante error |
| `tests/integration/test_e2e_advisor.py` | 4 | reporte sin/con settings, settings roundtrip, RLS |
| `frontend/src/api/advisor-api.test.ts` | 3 | report query, sin período, update settings |
| `frontend/src/lib/advisor.test.ts` | 3 | buckets, severidad→badge, formatPct |

## Pendientes técnicos (deuda conocida)
- [ ] **Caché de la narración LLM — PENDIENTE (Fase 9.1).** Hoy, con `advisor_llm_provider=claude`, cada
  `GET /advisor/report` hace ~N+1 llamadas a la API (una por insight + síntesis), **sin caché**. A implementar:
  cachear la salida del LLM por `(tenant, fingerprint de insights + modelo + versión de prompt)` detrás de un port,
  idealmente una **tabla en Postgres con RLS** (migración 0012) + TTL. Los **KPIs siempre se recalculan frescos**;
  sólo se cachea la redacción. Con `off` (default) no aplica. TODO marcado en `application/advisor/report.py`.
- [ ] **Antes de prender `claude` en prod:** set de evals de alucinación + agregar dep `anthropic` a `pyproject`
  (hoy import lazy; si falta, cae en silencio a plantillas) + `ANTHROPIC_API_KEY`. En dev/tests queda off.

## Config (env vars, NO hardcodeadas)
`ADVISOR_LLM_PROVIDER` (off|claude, default off), `ANTHROPIC_API_KEY`, `ADVISOR_LLM_MODEL` (default
`claude-opus-4-8`). Documentadas en `backend/.env.example`. El literal en `config.py` es sólo el default overridable
por entorno; el modelo y la key se cambian en Railway sin tocar código (reiniciar el servicio para tomarlas).

## Next Steps
- [ ] Code review via `/code-review`
- [x] Merge a `main` — `origin/main` = `e313480`
- [ ] **Fase 10 — Reportes (Excel/contador) + WhatsApp del lunes** (consume el reporte del asesor).
