import type { FloorTableDTO } from "@/api/types-operations"
import { floorView } from "@/lib/floor-session"

// Resumen del salón para el snapshot del Home: cuántas mesas en cada estado. Puro
// (reusa floorView, la misma derivación que el tablero) → testeable.
export interface FloorSummary {
  total: number
  free: number
  occupied: number
  toServe: number
  toCharge: number
}

export function floorSummary(tables: FloorTableDTO[]): FloorSummary {
  const s: FloorSummary = { total: tables.length, free: 0, occupied: 0, toServe: 0, toCharge: 0 }
  for (const t of tables) {
    const state = floorView(t).state
    if (state === "FREE") s.free += 1
    else s.occupied += 1
    if (state === "TO_SERVE") s.toServe += 1
    if (state === "TO_CHARGE" || state === "SERVED") s.toCharge += 1
  }
  return s
}
