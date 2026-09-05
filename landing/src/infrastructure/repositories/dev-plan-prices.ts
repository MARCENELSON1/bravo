import type { Currency } from "@/domain/value-objects/money"
import type { Region } from "@/domain/value-objects/region"

// Precios de respaldo SOLO PARA DESARROLLO.
//
// El catálogo real vive en el backend (GET /public/plans, editable desde el panel):
// esa sigue siendo la única fuente de verdad. Pero sin backend levantado la sección
// de Planes queda vacía, y no se puede trabajar en la vidriera. Con esto la página
// se ve completa mientras se desarrolla.
//
// AR: son los precios que tenía el repo antes de mover el catálogo al panel.
// INTL: son PROVISORIOS. No hay ningún precio en USD en el repositorio, así que
//       estos son un placeholder para poder ver el diseño — hay que reemplazarlos
//       por los reales. Nunca se sirven en producción (ver HttpPlanRepository).
export interface DevPrice {
  readonly amount: number
  readonly currency: Currency
}

export const DEV_PLAN_PRICES: Readonly<Record<Region, Readonly<Record<string, DevPrice>>>> = {
  AR: {
    BASIC: { amount: 0, currency: "ARS" },
    PRO: { amount: 29900, currency: "ARS" },
    ENTERPRISE: { amount: 59900, currency: "ARS" },
  },
  INTL: {
    BASIC: { amount: 0, currency: "USD" },
    PRO: { amount: 49, currency: "USD" },
    ENTERPRISE: { amount: 99, currency: "USD" },
  },
}

// El orden en que se muestran cuando se usa el respaldo.
export const DEV_TIER_ORDER = ["BASIC", "PRO", "ENTERPRISE"] as const
