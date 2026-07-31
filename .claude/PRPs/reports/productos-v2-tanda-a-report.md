# Implementation Report: Productos v2 — Tanda A (menu engineering)

**Fecha:** 2026-07-30 · **Rama:** `feat/productos-v2-a`

## Summary
Primera tanda de Productos v2 (XL). **Frontend puro, sin backend ni migraciones**: reusa el endpoint existente `GET /analytics/products` (`useProductPerformance`) para clasificar la carta en las 5 categorías de menu engineering. Las tandas B (precios vs inflación) y C (recetas madre) quedan pendientes en el plan.

## Validación
| Check | Estado |
|---|---|
| Build (tsc+vite) | ✅ |
| Tests front | ✅ 132 passed (7 nuevos: clasificación + top/killers) |
| Lint | ✅ |
| Backend | N/A (sin cambios) |

## Lo entregado
- **`menu-engineering.ts`** (helper puro, testeado): `classifyMenu` clasifica cada producto en `funciona / oportunidad / estable / revisar / no_vendido` según margen% y volumen (derivados de `ProductPerformanceRow`), + `topEarners` + `marginKillers`. Umbrales explícitos (HIGH_MARGIN 55%, LOW_MARGIN 45%).
- **`menu-engineering-view.tsx`** (componente): hero "Tu carta este mes", 5 tarjetas por categoría (con acción + top platos + margen total), top 3 que más plata dejan, y tabla de detalle (Precio/Costo/Te deja/Vendidos/Estado). Ventana: últimos 30 días.
- **`products-page.tsx`**: renderiza `MenuEngineering` arriba del catálogo; container ensanchado a `max-w-7xl`.

## Desviaciones
- Componente renombrado a `menu-engineering-view.tsx` para evitar colisión de basename con el helper `menu-engineering.ts` (el import con `.tsx` explícito rompía el build).
- "Asesinos de margen" quedó cubierto por la categoría "Revisar" (mismo criterio: vende pero margen <45%) en vez de una card aparte.

## Pendiente (Tandas B y C — en el plan `productos-v2.plan.md`)
- **Tanda B**: precios vs inflación + simulador + rotación por día (migración 0020: histórico de precios + inflación).
- **Tanda C**: recetas madre/anidadas (migración 0021: sub-recetas + food cost multinivel — la más riesgosa, toca el motor de Finanzas).

## Next Steps
- [ ] Revisión visual en el navegador (claro/oscuro).
- [ ] Tanda B (`/prp-implement productos-v2.plan.md` → sección Tanda B) en sesión nueva.
