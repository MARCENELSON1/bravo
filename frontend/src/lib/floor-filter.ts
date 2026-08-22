import type { FloorTableDTO } from "@/api/types-operations"
import { floorView } from "@/lib/floor-session"

// The floor chips (§5.2): quick lenses onto the salon. "A cobrar" groups the
// tables the party has finished with (servida or a_cobrar); "Mis mesas" needs
// the current user's id.
export type FloorChip = "all" | "to_serve" | "to_charge" | "mine" | "free"

function matchesChip(
  table: FloorTableDTO,
  chip: FloorChip,
  currentUserId?: string | null
): boolean {
  if (chip === "all") return true
  const view = floorView(table)
  switch (chip) {
    case "to_serve":
      return view.state === "TO_SERVE"
    case "to_charge":
      return view.state === "TO_CHARGE" || view.state === "SERVED"
    case "mine":
      return view.waiterId != null && view.waiterId === currentUserId
    case "free":
      return view.state === "FREE"
  }
}

// Filters the salon by a chip lens and a free-text search (table number or name).
export function filterFloor(
  tables: FloorTableDTO[],
  search: string,
  chip: FloorChip,
  currentUserId?: string | null
): FloorTableDTO[] {
  const q = search.trim().toLowerCase()
  return tables.filter((t) => {
    if (!matchesChip(t, chip, currentUserId)) return false
    if (q === "") return true
    return String(t.number).includes(q) || (t.name ?? "").toLowerCase().includes(q)
  })
}
