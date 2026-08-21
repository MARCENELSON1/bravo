import type { Money } from "@/domain/value-objects/money"

// Un ítem de la lista de features de un plan. `included=false` se muestra tachado.
export interface PlanFeature {
  readonly label: string
  readonly included: boolean
}

export type BillingPeriod = "monthly" | "yearly"

// Entidad de dominio: un plan de precios. Guarda el precio mensual y el precio
// mensual-equivalente cuando se factura anual (ya con descuento aplicado).
export interface Plan {
  readonly id: string
  readonly name: string
  readonly tagline: string
  readonly monthlyPrice: Money
  readonly yearlyPrice: Money
  readonly featured: boolean
  readonly badge?: string
  readonly ctaLabel: string
  readonly features: readonly PlanFeature[]
}

/** Precio a mostrar según el período elegido. Regla de negocio pura. */
export function priceFor(plan: Plan, period: BillingPeriod): Money {
  return period === "yearly" ? plan.yearlyPrice : plan.monthlyPrice
}
