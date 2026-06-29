// Selector temporal de la Pantalla Finanzas (del doc: Hoy / Esta semana / Este
// mes / Trimestre). Convierte el preset en una ventana { from, to } ISO usando
// los límites locales del día; el backend la consume como since/until.

export type FinanceRange = "today" | "week" | "month" | "quarter"

export interface RangeWindow {
  from: string // ISO
  to: string // ISO
}

export const FINANCE_RANGES: { value: FinanceRange; label: string }[] = [
  { value: "today", label: "Hoy" },
  { value: "week", label: "Esta semana" },
  { value: "month", label: "Este mes" },
  { value: "quarter", label: "Trimestre" },
]

function startOfDay(d: Date): Date {
  return new Date(d.getFullYear(), d.getMonth(), d.getDate())
}

// Lunes como primer día de la semana (rioplatense).
function startOfWeek(d: Date): Date {
  const day = startOfDay(d)
  const weekday = (day.getDay() + 6) % 7 // 0 = lunes
  day.setDate(day.getDate() - weekday)
  return day
}

function startOfQuarter(d: Date): Date {
  const q = Math.floor(d.getMonth() / 3) * 3
  return new Date(d.getFullYear(), q, 1)
}

export function rangeWindow(range: FinanceRange, now: Date = new Date()): RangeWindow {
  let from: Date
  switch (range) {
    case "today":
      from = startOfDay(now)
      break
    case "week":
      from = startOfWeek(now)
      break
    case "quarter":
      from = startOfQuarter(now)
      break
    case "month":
    default:
      from = new Date(now.getFullYear(), now.getMonth(), 1)
      break
  }
  return { from: from.toISOString(), to: now.toISOString() }
}
