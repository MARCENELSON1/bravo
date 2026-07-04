# Implementation Report: Pantalla Finanzas — Tanda A

## Summary
Primera tanda del plan `pantalla-finanzas.plan.md`: la **Pantalla Finanzas unificada** (`/app/finanzas`) con los KPIs vitales que ya tienen data (prime/food/labor/mermas como ratios + net/gross margin + break-even), cada uno con **comparativo vs período previo** y **rango sano** coloreado, los **diagnósticos narrados** del Asesor, el **margen de contribución por producto** y el **selector temporal** (Hoy/Semana/Mes/Trimestre). Compone `GetAdvisorReport` + `GetProductPerformance` sin reescribir la inteligencia ni agregar SQL/migraciones.

## Assessment vs Reality
| Metric | Predicho (plan) | Real |
|---|---|---|
| Complejidad (Tanda A) | parte de XL | Medium-Large, single-pass |
| Confidence | 8/10 | cumplido (sin retrabajo) |
| Files | ~17 | 22 (incl. plan + 3-file registration) |

## Tasks Completed
| # | Task | Status | Notes |
|---|---|---|---|
| 1 | `AdvisorReport.previous` para Δ | ✅ | Cambio mínimo, no rompe el asesor |
| 2 | `application/finance` (DTOs + GetFinanceOverview) | ✅ | Reusa advisor + product performance |
| 3 | `GET /finance/overview` + schemas | ✅ | Roles OWNER/MANAGER |
| 4 | Wiring container + main.py | ✅ | |
| 5 | Frontend: api+hook+lib+page+registro+ruta+nav | ✅ | |
| 6 | Tests backend + frontend | ✅ | |

## Validation Results
| Level | Status | Notes |
|---|---|---|
| Static (ruff+mypy) | ✅ | 280 archivos mypy ok |
| Unit | ✅ | 6 unit finance + suite |
| Build (front) | ✅ | tsc -b + vite build |
| Integration | ✅ | 3 e2e finance |
| Backend suite | ✅ | 335 passed |
| Frontend suite | ✅ | 114 passed |

## Deviations from Plan
- **Read model**: en vez de crear `FinanceOverviewReadModel` + `SqlAlchemyFinanceOverviewReadModel` paralelos, `GetFinanceOverview` **compone los use cases existentes** (advisor + product performance). Es más limpio (una sola fuente de métricas) y el swap de snapshots (Tanda F) ocurre a nivel del read model del Asesor, beneficiando a Finanzas automáticamente. Documentado para Tanda F.
- **Selector "Comparar períodos"**: el doc lista 5 opciones; se implementaron los 4 presets (Hoy/Semana/Mes/Trimestre). El comparativo vs período previo **ya está** (Δ en cada KPI). El picker custom "Comparar" se difiere a Tanda B.
- **Plan NO archivado**: quedan 5 tandas (B-F); el plan sigue en `plans/` (no en `completed/`).

## Files Changed
22 archivos: 11 backend (3 nuevos finance + advisor/container/main + 2 tests), 11 frontend (finance-api/hook/range/page + types + registro 3 archivos + router/nav + 2 tests). Merge `fd78751`.

## Next Steps
- [ ] Tanda B — proyección de cierre + drill-down + "Comparar" custom
- [ ] Tanda C — diagnostics cacheados (Fase 9.1)
- [ ] Tanda D — labor desde horas reales
- [ ] Tanda E — RevPASH + rotación
- [ ] Tanda F — capa de snapshots
