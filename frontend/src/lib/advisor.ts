import { numberLocale } from "@/lib/format"

// Insight buckets, in display order (Actuá hoy → Bien hecho).
export const BUCKET_ORDER = ["TODAY", "THIS_WEEK", "UPCOMING", "WELL_DONE"] as const

export const BUCKET_LABELS: Record<string, string> = {
  TODAY: "Actuá hoy",
  THIS_WEEK: "Esta semana",
  UPCOMING: "Lo que viene",
  WELL_DONE: "Bien hecho",
}

type BadgeVariant = "default" | "secondary" | "outline" | "destructive" | "warning"

export const SEVERITY_VARIANT: Record<string, BadgeVariant> = {
  GOOD: "default",
  INFO: "outline",
  WARN: "warning",
  CRITICAL: "destructive",
}

// Tono del resumen: el recuadro de arriba no puede dar una buena noticia cuando
// abajo hay diagnósticos críticos. Se queda con el peor estado del informe.
export type SummaryTone = "good" | "warn" | "critical"

const SEVERITY_RANK: Record<string, number> = { GOOD: 0, INFO: 1, WARN: 2, CRITICAL: 3 }

export function summaryTone(report: {
  insights: readonly { severity: string }[]
  kpis: { configured: boolean; net_margin_amount: number }
}): SummaryTone {
  // Perder plata es crítico aunque el detalle todavía no lo enuncie.
  if (report.kpis.configured && report.kpis.net_margin_amount < 0) return "critical"
  const worst = report.insights.reduce(
    (max, insight) => Math.max(max, SEVERITY_RANK[insight.severity] ?? 0),
    0
  )
  if (worst >= SEVERITY_RANK.CRITICAL) return "critical"
  if (worst >= SEVERITY_RANK.WARN) return "warn"
  return "good"
}

// Basis points → percent label (e.g. 3300 → "33%").
export function formatPct(bps: number): string {
  return `${(bps / 100).toLocaleString(numberLocale(), { maximumFractionDigits: 1 })}%`
}
