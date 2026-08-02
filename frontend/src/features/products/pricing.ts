import type { PricingRowDTO } from "@/api/types-operations"

// Helpers puros de Productos v2 Tanda B (precios vs inflación + rotación).

export const WEEKDAY_LABELS = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"] as const

export function weekdayLabel(weekday: number): string {
  return WEEKDAY_LABELS[weekday] ?? "?"
}

// Basis points → texto de porcentaje (2000 bps = "20%").
export function bpsToPct(bps: number, digits = 1): string {
  return `${(bps / 100).toFixed(digits)}%`
}

export interface PricingSummary {
  laggingCount: number
  worst: PricingRowDTO | null
}

// Resumen para el hero: cuántos precios quedaron atrás y cuál es el más rezagado.
export function pricingSummary(rows: PricingRowDTO[]): PricingSummary {
  const lagging = rows.filter((r) => r.lagging)
  const worst = lagging.reduce<PricingRowDTO | null>(
    (max, r) => (max === null || r.gap_bps > max.gap_bps ? r : max),
    null
  )
  return { laggingCount: lagging.length, worst }
}
