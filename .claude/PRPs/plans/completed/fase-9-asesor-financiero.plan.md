# Plan: Fase 9 — Asesor financiero + Dashboard (insights proactivos)

## Summary
La **Capa 2** arranca: sobre el modelo canónico (Fase 8) montamos el **asesor financiero que habla en pesos** —
KPIs avanzados (food/labor/prime cost, **margen neto**, **punto de equilibrio**, mermas) + **insights proactivos**
agrupados en *Actuá hoy / Esta semana / Lo que viene / Bien hecho*, y un **dashboard del asesor**. Arquitectura en
**dos capas**: un **piso determinístico** (fuente de verdad, siempre corre, testeable, gratis) y una **capa LLM
grounded** (Claude narra/sintetiza sobre los números ya calculados, detrás de un port, **apagada por default**).
Prioridad PRD: el asesor es el diferenciador (KPIs→conclusiones→una acción concreta). Depende de Fase 8.

> **DECISIONES DE ARQUITECTURA (cerradas con el usuario — no re-litigar):**
> 1. **Dos capas, una sola verdad.** El **piso determinístico** calcula KPIs y detecta insights con reglas puras
>    sobre el modelo canónico; los **números son SIEMPRE exactos**. La **capa LLM** se monta ENCIMA: recibe los
>    KPIs/insights ya calculados y solo **narra** (redacta en español "en pesos") y **sintetiza** (resumen, prioriza).
> 2. **El LLM NUNCA hace cuentas ni inventa cifras.** Se lo alimenta con los números del canónico y se le prohíbe
>    calcular. Guardrail liviano: si la salida introduce un número que no está en el set provisto, se descarta y cae
>    a plantilla. Los números mostrados vienen SIEMPRE del piso determinístico.
> 3. **LLM detrás de port + `Selector`, apagado por default.** `InsightNarrator` (`template`|`claude`) y
>    `AdvisorSynthesizer` (`none`|`claude`) — mismo patrón que `payment_gateway`/`invoicing_provider`. Se prende por
>    config cuando exista un **set de evals de alucinación** (open question del PRD). **Cacheado** (una llamada por
>    tenant/período, no por carga).
> 4. **Degradación elegante.** Sin configurar costos, el asesor igual muestra lo que sale del canónico (food cost
>    ratio, margen bruto, no-shows, productos que pierden plata). Con `AdvisorSettings` (costos fijos + sueldos)
>    desbloquea labor/prime cost, **punto de equilibrio** y **margen neto**.
> 5. **Distinto del copiloto (Fase 11).** Este asesor está **acotado**: narra/sintetiza sobre KPIs pre-calculados.
>    El copiloto conversacional libre (text-to-SQL con guardrails) sigue siendo Fase 11. No se mezclan.
> 6. **Money entero + moneda del tenant**; multi-tenant + RLS; el piso es Python puro y testeable (≥80%).

## Estado de implementación
PENDIENTE. Depende de Fase 8 (modelo canónico) — ✅ en `main`. Consume además Fase 5 (horas), 6 (food cost/mermas),
7 (no-shows). Se implementa en rama `feat/fase-9-asesor-financiero`. Migración nueva: **0011_advisor_settings**.

## User Story
Como **dueño/encargado** quiero **abrir el asesor y que me diga en pesos cómo me fue y qué hacer** (3–4 acciones
concretas priorizadas), para **decidir compras/precios/turnos sin cruzar planillas ni interpretar % sueltos**.

## Problem → Solution
Hoy hay datos (Fase 8) pero no **lectura**: el dueño no sabe si su food cost está alto, si llega al punto de
equilibrio, ni qué plato le hace perder plata. → KPIs avanzados en pesos + un motor de **insights** que traduce cada
métrica a *una conclusión con una acción*, agrupados por urgencia; la capa LLM lo redacta natural cuando se habilita.

---

## Arquitectura en capas

```
PISO DETERMINÍSTICO (dominio puro, fuente de verdad)        CAPA LLM (grounded, opcional, flag off)
─────────────────────────────────────────────────          ──────────────────────────────────────
KPIs avanzados (kpis.py):                                   InsightNarrator (Selector template|claude)
  food/labor/prime cost ratio, contribution margin,           template → texto fijo ES (default)
  break_even_sales, net_margin                                claude   → redacta el insight (grounded)
detect_insights(kpis, settings, prev) -> [Insight]          AdvisorSynthesizer (Selector none|claude)
  Insight{code, severity, bucket, data:{números}}             none   → sin resumen (default)
  buckets: TODAY/THIS_WEEK/UPCOMING/WELL_DONE                  claude → resumen del período (grounded)
                                                            Guardrail: descarta números ajenos → cae a plantilla
                                                            Caché por (tenant, período)
```

## Modelo de dominio (nuevo: `advisor`)
- **`AdvisorSettings`** (1:1 con tenant): `tenant_id, monthly_labor_cost (Money), monthly_other_fixed_costs (Money),
  target_food_cost_bps (int, default 3000=30%), currency`. Métodos de validación (montos ≥ 0).
- **KPIs puros (`kpis.py`, estilo `costing.py`/`taxation.py`):**
  - `food_cost_ratio_bps(sales, food_cost)`, `labor_cost_ratio_bps(sales, labor)`, `prime_cost_ratio_bps`.
  - `contribution_margin_ratio_bps(sales, variable_costs)`; `break_even_sales(fixed_costs, contribution_margin_bps)`.
  - `net_margin(sales, food_cost, labor, other_fixed)` (puede ser negativo → int).
  - Prorrateo mensual→período por días (documentado; el período del asesor es configurable, default "este mes").
- **`Insight`** (VO): `code, severity (GOOD|INFO|WARN|CRITICAL), bucket (TODAY|THIS_WEEK|UPCOMING|WELL_DONE),
  data (dict de números)`. **`detect_insights(...)`** puro → reglas: food cost > target (WARN/CRITICAL), por debajo
  del punto de equilibrio (CRITICAL), producto con margen < 0 (WARN), no-show alto (WARN), margen subió vs período
  previo (GOOD), prime cost > 60% (WARN), etc. (lista cerrada y testeable; severidad + bucket por regla).
- **Ports:** `AdvisorSettingsRepository`; `InsightNarrator` (`narrate(insight) -> NarratedInsight{title, body,
  action}`); `AdvisorSynthesizer` (`synthesize(report) -> str | None`).
- **Excepciones:** `InvalidAdvisorSettings` (code EN + message ES).

## Read model / composición
- **`AdvisorReadModel`** (o el use case compone los existentes): junta `RevenueReadModel`/`ProductPerformanceReadModel`
  (Fase 8) + `StaffReportReadModel` (Fase 5, horas) + mermas (Σ `stock_movements` WASTE valorizadas, Fase 6) +
  no-shows (Fase 7) + el **período previo** (misma duración inmediatamente anterior, para tendencias). Todo
  tenant-scoped + RLS. No requiere tabla nueva más allá de `advisor_settings`.

## Capa LLM (infra)
- **`ClaudeNarrator`** / **`ClaudeSynthesizer`** (adapter Anthropic): system prompt que **prohíbe calcular**, exige
  español rioplatense + "una sola acción concreta", recibe los KPIs/insights como JSON grounded. Output validado
  (no introducir cifras nuevas) y **cacheado**. Config: `advisor_llm_provider` (off|claude), `anthropic_api_key`,
  `advisor_llm_model`. Default **off** → `TemplateNarrator` + `NoSynthesis`.

## Config
- `advisor_default_period` (mes), `advisor_llm_provider=off`, `anthropic_api_key`, `advisor_llm_model`,
  `advisor_cache_ttl_min`.

---

## Mandatory Reading (moldes ya en el repo)
- **Modelo canónico (fuente):** `application/analytics/{read_models,use_cases}.py`,
  `infrastructure/persistence/analytics_repo.py`; `application/reporting/staff.py` + `staff_report_repo.py`;
  `domain/inventory/costing.py` (KPI puro), `domain/inventory/value_objects.py` (mermas/WASTE).
- **Selector de adapter + flag (molde para el LLM):** `container.py` (`payment_gateway`/`invoicing_provider`
  `providers.Selector`), `infrastructure/payments/{manual_gateway,mercadopago_gateway}.py`,
  `infrastructure/invoicing/{fake_invoicing,afip_invoicing}.py`, `config.py`.
- **Persistencia 1:1 + RLS + Fernet (molde settings):** `domain/invoice/credentials.py` +
  `tax_credentials_repo.py` (1:1 por tenant), `alembic/versions/0010_sale_facts.py`, `models.py`, `mappers.py`.
- **Money / KPI puro:** `domain/shared/money.py`, `domain/inventory/costing.py`, `domain/invoice/taxation.py`.
- **API + RBAC + errores + router:** `presentation/api/v1/{analytics,reports}.py`, `rbac.py`, `errors.py`, `main.py`.
- **Frontend:** `features/analytics/analytics-page.tsx` (KPIs en pesos), `features/dashboard/dashboard-page.tsx`,
  `api/analytics-api.ts` + `hooks/use-analytics.ts`, `lib/analytics.ts`, `services/*`, `nav-config.ts`, `router.tsx`.

## Files to Change (orientativo)
**Backend (nuevos):** `domain/advisor/{__init__,entities,value_objects,kpis,insights,exceptions,repository,ports}.py`,
`application/advisor/{__init__,use_cases,report}.py`, `infrastructure/persistence/advisor_settings_repo.py`,
`infrastructure/advisor/{template_narrator,claude_narrator,no_synthesis,claude_synthesizer}.py`,
`presentation/api/v1/advisor.py`, `presentation/schemas/advisor.py`, `alembic/versions/0011_advisor_settings.py`,
tests unit + e2e (con LLM fake).
**Backend (editar):** `models.py`, `mappers.py`, `container.py`, `presentation/errors.py`, `main.py`, `config.py`,
`tests/integration/conftest.py` (`_TABLES` ← prepend `advisor_settings`), `pyproject.toml` (dep `anthropic`).
**Frontend (nuevos):** `api/{types-advisor,advisor-api}.ts` (+ test), `hooks/use-advisor.ts`, `lib/advisor.ts`
(+ test), `features/advisor/advisor-page.tsx`, `features/advisor/advisor-settings-sheet.tsx`.
**Frontend (editar):** `services/services-{context,provider}`, `test/test-utils.tsx`, `nav-config.ts`
(Resumen → "Asesor"), `app/router.tsx`.

---

## Step-by-Step Tasks

### T1 — Dominio advisor (piso determinístico) + settings
- `AdvisorSettings` (entidad + validación), `kpis.py` (food/labor/prime cost ratio, contribution margin,
  break_even_sales, net_margin — puros), `Insight` VO + `detect_insights` (reglas, severidad, bucket), excepciones,
  ports. ORM `advisor_settings` + mapper + repo (1:1) + **migración 0011** (RLS). `conftest._TABLES`.
- **Tests unit:** cada KPI (incl. casos borde: sales=0, margen negativo), break-even, y cada regla de
  `detect_insights` (dispara/no dispara, severidad, bucket).
- **MIRROR:** `domain/inventory/costing.py`, `domain/invoice/taxation.py`, `tax_credentials_repo.py`,
  `0010_sale_facts.py`.

### T2 — Read model + reporte determinístico (narración por plantilla)
- `application/advisor/report.py`: compone canónico + staff + mermas + no-shows + **período previo** → KPIs.
  `GetAdvisorReport` (KPIs + `detect_insights` + narración con `TemplateNarrator` por default; sin LLM). Use cases
  `GetAdvisorSettings`/`UpdateAdvisorSettings`.
- **Tests e2e (sin LLM):** con comandas PAID + costos configurados → food cost ratio, prime cost, break-even,
  margen neto, insights agrupados correctos; sin settings → degradación elegante; RLS.
- **MIRROR:** `application/analytics/use_cases.py` + `analytics_repo.py`, `application/reporting/staff.py`.

### T3 — API + RBAC (asesor shippable sin LLM)
- Router `/advisor/*`: `GET /advisor/report` (from/to), `GET /advisor/settings`, `PUT /advisor/settings`
  (OWNER/MANAGER; settings OWNER). Container + `errors.py` (`InvalidAdvisorSettings`=422) + `main.py`.
- **Tests e2e:** report end-to-end; settings GET/PUT; RLS.
- **MIRROR:** `presentation/api/v1/{analytics,tax}.py`, `rbac.py`.

### T4 — Capa LLM (grounded, flag off por default)
- Ports `InsightNarrator` (Selector `template`|`claude`) + `AdvisorSynthesizer` (Selector `none`|`claude`).
  Adapters: `TemplateNarrator`/`NoSynthesis` (default) y `ClaudeNarrator`/`ClaudeSynthesizer` (Anthropic, grounded,
  **prohibido calcular**, output validado contra el set de números, **cacheado**). Config flags. `GetAdvisorReport`
  usa el narrator inyectado + (opcional) synthesizer. Dep `anthropic`.
- **Tests:** con un **fake LLM** (no llama a la red): narración usa el LLM cuando `claude`; el **guardrail** descarta
  una cifra inventada y cae a plantilla; con `off` el reporte es idéntico a T2 (determinístico).
- **MIRROR:** `infrastructure/payments/*` + `payment_gateway` Selector; `infrastructure/invoicing/fake_invoicing.py`.

### T5 — Frontend: dashboard del asesor + settings
- `AdvisorApi` + `use-advisor` hooks; registrar en services + test-utils. `lib/advisor.ts` (labels de bucket/severidad,
  formato). Página **Asesor** (`/app/advisor`, OWNER/MANAGER): KPIs en pesos (food/labor/prime cost, margen neto,
  punto de equilibrio, mermas) + **insights agrupados** (Actuá hoy / Esta semana / Lo que viene / Bien hecho) con su
  acción + (si hay) narrativa del synthesizer + estado del LLM (on/off). Sheet de **costos** (`AdvisorSettings`).
  Nav "Asesor" en Resumen + ruta. (Onboarding por rubro = prefill de targets, **opcional**; si aprieta, diferir.)
- **Validar:** tsc + eslint + vitest + build.
- **MIRROR:** `features/analytics/analytics-page.tsx`, `features/integrations/integrations-page.tsx` (estado de
  conexión/flag), `hooks/use-analytics.ts`, `api/analytics-api.ts`.

---

## Validation Commands
- **Backend:** `poetry run ruff check app tests` · `poetry run mypy app` · `poetry run pytest -q` (≥80% en
  domain/application). **El LLM nunca se llama en tests** (fake adapter).
- **Frontend:** `npx tsc --noEmit` · `npx eslint src` · `npx vitest run` · `npx vite build`.

## Acceptance Criteria
- Con comandas PAID + costos configurados, el `GET /advisor/report` devuelve **food/labor/prime cost ratio, margen
  neto, punto de equilibrio y mermas** correctos (números del modelo canónico) + **insights** agrupados en los 4
  buckets con su acción concreta.
- **Sin** costos configurados, el asesor degrada (muestra lo derivable del canónico + pide configurar costos).
- La **capa LLM** está detrás de `Selector` y **apagada por default**: con `off` el reporte es 100% determinístico;
  con `claude` (fake en tests) narra/sintetiza **sin alterar los números** (guardrail probado).
- Scoped por tenant (RLS). ruff + mypy + pytest + tsc + eslint + vitest + build en verde.

## Complexity / Confidence
- **Complejidad:** Alta. Es la fase más grande: KPIs financieros + motor de insights + capa LLM grounded + dashboard.
  El piso (T1–T3) es puro/SQL sobre patrones probados (alta confianza). La capa LLM (T4) es lo nuevo: el riesgo está
  en el grounding/guardrail, mitigado por el flag off + fake en tests.
- **Confianza:** Alta en T1–T3 y T5. Media en T4 (integración LLM; pero aislada y opcional).

## Out of scope (diferido)
- **Copiloto conversacional** (text-to-SQL libre con guardrails) → **Fase 11**. Reporte para el contador (Excel + IVA)
  y **WhatsApp del lunes** → **Fase 10**. Evals formales de alucinación del LLM (set + harness) — pre-requisito para
  **prender** el flag en prod, no para mergear (en dev queda off). Proyección de costos fijos por sub-rubro /
  benchmarks de industria; pronósticos/forecast; alertas push. CRM de clientes → Fase 12.
