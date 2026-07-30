// Veredicto del día en lenguaje del dueño (Home Nivel 1). Función pura y testeable.
// `net` = ganancia neta del día (minor units). `pctVsYesterday` = variación de la
// facturación de hoy vs ayer (null si no hay dato de ayer).

export type VerdictTone = "good" | "ok" | "bad"

export interface DailyVerdict {
  tone: VerdictTone
  message: string
}

export function dailyVerdict(net: number, pctVsYesterday: number | null): DailyVerdict {
  const vs =
    pctVsYesterday === null
      ? ""
      : pctVsYesterday >= 0
        ? ` — ${Math.round(pctVsYesterday)}% más que ayer`
        : ` — ${Math.round(Math.abs(pctVsYesterday))}% menos que ayer`

  if (net < 0) {
    return { tone: "bad", message: `Día para revisar${vs}` }
  }
  if (pctVsYesterday !== null && pctVsYesterday < 0) {
    return { tone: "ok", message: `Día normal${vs}` }
  }
  return { tone: "good", message: `Buen día${vs}` }
}
