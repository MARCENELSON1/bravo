import { describe, expect, it } from "vitest"

import type {
  FloorSessionDTO,
  FloorTableDTO,
  OrderDTO,
  SessionState,
} from "@/api/types-operations"
import { filterFloor } from "@/lib/floor-filter"

const order = (status: OrderDTO["status"]): OrderDTO => ({
  id: "o",
  table_id: "t",
  waiter_id: "w",
  status,
  currency: "ARS",
  items: [],
  total_amount: 0,
  created_at: null,
  customer_id: null,
})

const session = (state: SessionState, waiterId: string | null = null): FloorSessionDTO => ({
  id: "s",
  state,
  state_since: null,
  pax: null,
  waiter_id: waiterId,
  waiter_name: null,
  sector_id: null,
})

const table = (
  number: number,
  name: string | null,
  ord: OrderDTO | null,
  sess: FloorSessionDTO | null = null
): FloorTableDTO => ({
  id: `t${number}`,
  number,
  name,
  status: ord ? "OCCUPIED" : "FREE",
  active_order: ord,
  session: sess,
  sector_id: null,
  capacity: null,
})

const tables = [
  table(1, "Ventana", order("SENT"), session("IN_KITCHEN", "juan")),
  table(2, "Barra", order("READY"), session("TO_SERVE", "juan")),
  table(3, "Patio", order("SERVED"), session("TO_CHARGE", "ana")),
  table(4, "Fondo", order("SERVED"), session("SERVED", "ana")),
  table(12, null, null),
]

describe("filterFloor", () => {
  it("returns all when chip is 'all' and no search", () => {
    expect(filterFloor(tables, "", "all")).toHaveLength(5)
  })

  it("matches by table number or name (case-insensitive)", () => {
    expect(filterFloor(tables, "barra", "all").map((t) => t.number)).toEqual([2])
    expect(filterFloor(tables, "2", "all").map((t) => t.number)).toEqual([2, 12])
  })

  it("'to_serve' keeps only tables with a ready dish", () => {
    expect(filterFloor(tables, "", "to_serve").map((t) => t.number)).toEqual([2])
  })

  it("'to_charge' groups servida + a_cobrar", () => {
    expect(filterFloor(tables, "", "to_charge").map((t) => t.number)).toEqual([3, 4])
  })

  it("'free' keeps only free tables", () => {
    expect(filterFloor(tables, "", "free").map((t) => t.number)).toEqual([12])
  })

  it("'mine' keeps only the current waiter's tables", () => {
    expect(filterFloor(tables, "", "mine", "juan").map((t) => t.number)).toEqual([1, 2])
  })

  it("falls back to the order status when there is no session", () => {
    const legacy = [table(7, "Vieja", order("READY"))]
    expect(filterFloor(legacy, "", "to_serve").map((t) => t.number)).toEqual([7])
  })
})
