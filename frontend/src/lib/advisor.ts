// Insight buckets, in display order (Actuá hoy → Bien hecho).
export const BUCKET_ORDER = ["TODAY", "THIS_WEEK", "UPCOMING", "WELL_DONE"] as const

export const BUCKET_LABELS: Record<string, string> = {
  TODAY: "Actuá hoy",
  THIS_WEEK: "Esta semana",
  UPCOMING: "Lo que viene",
  WELL_DONE: "Bien hecho",
}

type BadgeVariant = "default" | "secondary" | "outline" | "destructive"

export const SEVERITY_VARIANT: Record<string, BadgeVariant> = {
  GOOD: "default",
  INFO: "outline",
  WARN: "secondary",
  CRITICAL: "destructive",
}

// Basis points → percent label (e.g. 3300 → "33%").
export function formatPct(bps: number): string {
  return `${(bps / 100).toLocaleString("es-AR", { maximumFractionDigits: 1 })}%`
}
