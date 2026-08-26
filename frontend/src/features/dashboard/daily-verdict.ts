// Veredicto del día en lenguaje del dueño (Home Nivel 1). Función pura y testeable.
// `net` = ganancia neta del día (minor units). `pctVsYesterday` = variación de la
// facturación de hoy vs ayer (null si no hay dato de ayer).
//
// Contrato i18n: no arma texto, devuelve claves + números. El componente compone
// el mensaje con `t("dashboard.verdict.<tone>")` + `t("dashboard.verdict.<vsKey>")`.

export type VerdictTone = "good" | "ok" | "bad"
export type VerdictVsKey = "vsMore" | "vsLess"

export interface DailyVerdict {
  tone: VerdictTone
  vsKey: VerdictVsKey | null
  pct: number | null
}

export function dailyVerdict(net: number, pctVsYesterday: number | null): DailyVerdict {
  const pct = pctVsYesterday === null ? null : Math.round(Math.abs(pctVsYesterday))
  const vsKey: VerdictVsKey | null =
    pctVsYesterday === null ? null : pctVsYesterday >= 0 ? "vsMore" : "vsLess"

  const tone: VerdictTone =
    net < 0 ? "bad" : pctVsYesterday !== null && pctVsYesterday < 0 ? "ok" : "good"

  return { tone, vsKey, pct }
}
