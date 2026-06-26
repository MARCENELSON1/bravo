import type { FloorTableDTO } from "@/api/types-operations"

// Filters the salon for the cashier/waiter: by table number or name, and
// optionally only tables ready to charge (their active order is SERVED).
export function filterFloor(
  tables: FloorTableDTO[],
  search: string,
  onlyToCharge: boolean
): FloorTableDTO[] {
  const q = search.trim().toLowerCase()
  return tables.filter((t) => {
    if (onlyToCharge && t.active_order?.status !== "SERVED") return false
    if (q === "") return true
    return String(t.number).includes(q) || (t.name ?? "").toLowerCase().includes(q)
  })
}
