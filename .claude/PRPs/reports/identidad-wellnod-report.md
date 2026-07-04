# Implementation Report: Identidad Wellnod

**Fecha:** 2026-07-04 · **Rama:** `feat/identidad-wellnod` (desde `main` = `49a10c1`)

## Summary
Identidad visual de `origin/tita` (commit `2497ebc`) portada selectivamente sobre `main` — sin merge de la rama. La app ahora es **Wellnod**: shell de paneles de vidrio flotantes (claro Y oscuro, tema según el SO), nav híbrida con gating por rol intacto, saludo con nombre real (`GET /me` + `users.name`), y el dashboard rediseñado **100% con datos reales** (incluido el endpoint nuevo de serie diaria).

## Assessment vs Reality
| Metric | Predicted (Plan) | Actual |
|---|---|---|
| Complexity | Large (~28 files) | Large (31 files) |
| Confidence | 8/10 | Una sola pasada, sin retrabajos |
| Migraciones | 1 (`0016_user_name`) | 1, aplicada a dev |

## Tasks Completed
| # | Task | Status |
|---|---|---|
| 1 | Inter + wellnod-mark + index.css desde tita | ✅ |
| 2 | Bypass auth dev (`VITE_AUTH_BYPASS`) | ✅ |
| 3 | Migración 0016 + `users.name` en 3 capas | ✅ |
| 4 | Onboarding captura nombre (opcional) | ✅ |
| 5 | `GET /me` (use case + router + wiring) | ✅ |
| 6 | Session extendida + `me()` → `/me` | ✅ |
| 7 | Campo "Tu nombre" en onboarding UI | ✅ |
| 8 | Nav híbrida (cobertura total de rutas) | ✅ |
| 9 | AppShell glass (claro + oscuro) | ✅ |
| 10 | Rename NÚCLEO/BRAVO → Wellnod (UI + emails + título) | ✅ |
| 11 | Validación Tanda Id-1 | ✅ |
| 12 | Serie diaria backend (`GET /analytics/revenue/daily`) | ✅ |
| 13 | Cliente + hook `useRevenueDaily` | ✅ |
| 14 | Dashboard Wellnod con datos reales | ✅ |
| 15 | Validación Tanda Id-2 | ✅ |

## Validation Results
| Level | Status | Notes |
|---|---|---|
| Static (tsc -b) | ✅ | 0 errores |
| Lint (eslint) | ✅ | 0 errores |
| Unit+Integración backend | ✅ | **353 passed** (8 nuevos: 3 GetMyProfile, 3 e2e /me, 2 e2e serie diaria con RLS) |
| Tests frontend | ✅ | **116 passed** (1 nuevo: revenueDaily) |
| Build (`npm run build`) | ✅ | gate real (tsc -b + vite build) |
| Migración | ✅ | `alembic upgrade head` → 0016 en dev; prod vía preDeploy Railway |
| Visual (claro/oscuro) | ✅ | Verificado con Chrome + bypass dev: shell, dashboard y login en ambos temas |

## Deviations from Plan
- **KPIs del dashboard:** se mantuvieron los 5 reales existentes (Ventas/Comandas/Ticket/Egresos/Neto) con el estilo de card de tita, en vez de los 4 inventados del mock. El margen bruto vive en `/app/finanzas`.
- **Card "Punto de equilibrio" del mock** → "Proyección de cierre del mes" con `FinanceProjectionDTO` real (como preveía el plan).
- **Tarjeta de diagnóstico:** usa `title` del insight como etiqueta (el mock usaba categorías inventadas OPORTUNIDAD/ALERTA).

## Issues Encountered
Ninguno bloqueante. Nota conocida (documentada en el plan): la serie diaria trunca por día en **UTC**; una venta de las 22:00 ART cae al día UTC siguiente. Aceptado como MVP.

## Files Changed
31 archivos (14 backend, 16 frontend, 1 plan): commit Tanda Id-1 `7de8dcf` (29 files) + Tanda Id-2 (12 files). Detalle en los diffs de los commits.

## Next Steps
- [ ] Merge `--no-ff` a `main` + push (deploy Railway aplica 0016 y prende todo).
- [ ] Onboarding real: probar el flujo completo con backend (email → login → saludo).
- [ ] Futuro: foto real de fondo, consolidación por pestañas del grupo Gestión, `date_trunc` con timezone del tenant.
- [ ] Retomar Finanzas D–F (migraciones renumeradas 0017/0018/0019).
