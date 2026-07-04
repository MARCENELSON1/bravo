# Reporte — Pantalla Finanzas Tanda C: diagnostics cacheados (Fase 9.1)

**Fecha:** 2026-07-04 · **Rama:** `feat/finanzas-tanda-c` → merge a `main`

## Qué se entregó
Los textos narrados del Asesor (insights + summary LLM) se generan **una vez** ante un cambio relevante y se sirven instantáneos desde Postgres; no se llama a la IA en cada apertura de `/app/finanzas` ni `/app/advisor`.

- **Tabla `advisor_diagnostics`** (tenant_id + fingerprint + payload JSON + generated_at) con **RLS** — migración `0015_advisor_diagnostics` (aplicada al dev DB; prod la aplica el preDeploy de Railway).
- **Port `AdvisorDiagnosticsCache`** (`domain/advisor/repository.py`) con `get`/`put`/`purge` + adapter `SqlAlchemyAdvisorDiagnosticsCache` (queries siempre filtradas por `tenant_id`, defensa en profundidad sobre RLS).
- **Caché en `GetAdvisorReport`**: fingerprint SHA-256 determinístico de los insights + proveedor. Mismo estado de datos → cache hit; cambia la data → cambia el hash → regenera y guarda. **Solo cachea con LLM prendido** (con narrador template es instantáneo y cachear sería escribir de más).
- **Rebuild manual**: `POST /advisor/diagnostics/rebuild` (OWNER) → `RebuildAdvisorDiagnostics` purga lo del tenant; el próximo request regenera.

## Validación
- **Unit (240 passed):** fingerprint estable y sensible a data/proveedor; cache hit no re-narra; cambio de data regenera; LLM off no cachea; rebuild purga solo el tenant y regenera.
- **Integración (105 passed, Postgres real):** `test_e2e_advisor_cache.py` — 2º request sirve del caché sin re-sintetizar (LLM prendido vía override del container con synthesizer contador; caché SQL y RLS reales); rebuild purga y regenera; rebuild de otro tenant purga 0 (aislamiento).
- Cobertura: `report.py` 100%; código nuevo cubierto.

## Notas de diseño
- La invalidación es **automática por fingerprint** (no hay TTL ni invalidación manual necesaria); el rebuild expuesto es botón de escape.
- El e2e del plan pedía comparar `generated_at`; se validó lo equivalente y más directo: contar llamadas al synthesizer (si no se llama, se sirvió del caché).
- Desvío del plan: ninguno funcional. Extra: `purge` devuelve el conteo para observabilidad del rebuild.

## Sigue
- Tanda D (labor desde horas, migración pasa a `0017` por la `0016_user_name` de Identidad Wellnod), E y F del plan `pantalla-finanzas.plan.md`.
