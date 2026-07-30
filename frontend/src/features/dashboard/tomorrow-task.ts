import type { FinanceDiagnosticDTO } from "@/api/types-operations"

// "Tu tarea para mañana" (Home Nivel 7): una sola acción concreta, derivada del
// diagnóstico más urgente del Asesor. Determinista (no LLM). null si todo sano.

const SEVERITY_RANK: Record<string, number> = { alert: 0, warn: 1, healthy: 2 }

export function tomorrowTask(diagnostics: FinanceDiagnosticDTO[]): string | null {
  const actionable = diagnostics
    .filter((d) => d.action && (d.severity === "alert" || d.severity === "warn"))
    .sort((a, b) => (SEVERITY_RANK[a.severity] ?? 9) - (SEVERITY_RANK[b.severity] ?? 9))
  return actionable[0]?.action ?? null
}
