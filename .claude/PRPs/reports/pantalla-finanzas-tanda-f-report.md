# Reporte — Pantalla Finanzas Tanda F: capa de snapshots

**Fecha:** 2026-07-04 · **Rama:** `feat/finanzas-tanda-f` → merge a `main`

## Qué se entregó
Capa 2 del doc: totales diarios pre-agregados para servir Finanzas sin escanear todo el historial de `sale_facts` (performance a escala). **Off by default** (modo `live`), reversible por flag.

- **Tabla `finance_daily_snapshots`** (tenant_id + day + sales/food_cost/orders/units) con **RLS** — migración `0019` (aplicada a dev; prod vía preDeploy).
- **Mantenimiento incremental** co-locado en `ProjectOrderSales`: al proyectar un cobro suma al snapshot del día; al revertir (reabrir orden) resta. Siempre activo → el snapshot queda caliente aunque el modo sea live.
- **Read model por snapshot** (`SqlAlchemyAdvisorSnapshotReadModel`): ventas/food/órdenes desde los snapshots del rango; **merma y no-show siguen live** (tablas chicas que no crecen con cada venta). Comparte las queries de merma/no-show con el modo live (refactor a helpers).
- **Selector por config** `finance_snapshots_read` (`live`|`snapshot`, default `live`) sobre `advisor_read_model` — afecta a Finanzas y al Asesor por igual.
- **Rebuild** `POST /finance/snapshots/rebuild` (OWNER) → reconstruye desde `sale_facts` agrupando por día. Necesario para backfill del historial previo antes de prender el modo snapshot.

## Decisión de diseño (scope)
La ganancia de performance es casi toda por no escanear `sale_facts` (crece con cada venta). Merma (`stock_movements` WASTE) y reservas son tablas chicas → se dejan live. Esto da la misma ganancia con **mucho menos riesgo** (un solo punto de co-locación incremental: el projector de ventas) y **paridad garantizada** en merma/no-show (mismo cálculo).

## Validación
- **Backend 368 passed** (3 e2e nuevos): paridad snapshot==live incremental (sin rebuild), un cobro nuevo actualiza el snapshot del día sin rebuild, y rebuild reconstruye con paridad + idempotente.
- Las 365 pruebas previas siguen verdes en modo live (default) → cero cambio de comportamiento en prod.

## Cómo prender en prod (cuando haga falta)
1. `POST /finance/snapshots/rebuild` por tenant (backfill).
2. Setear `FINANCE_SNAPSHOTS_READ=snapshot` en el `api` de Railway.
No urge: recién rinde con meses de historial; hoy no hay diferencia perceptible.

## Cierre
**Pantalla Finanzas COMPLETA** (Tandas A–F). Los 7 KPIs del doc + comparativos + proyección + diagnósticos cacheados + labor real + RevPASH/rotación + capa de snapshots.
