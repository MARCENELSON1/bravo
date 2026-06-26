import { describe, expect, it } from "vitest"

import type { FloorTableDTO, OrderDTO } from "@/api/types-operations"
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
})

const table = (number: number, name: string | null, ord: OrderDTO | null): FloorTableDTO => ({
  id: `t${number}`,
  number,
  name,
  status: ord ? "OCCUPIED" : "FREE",
  active_order: ord,
})

const tables = [
  table(1, "Ventana", order("OPEN")),
  table(2, "Barra", order("SERVED")),
  table(12, null, null),
]

describe("filterFloor", () => {
  it("returns all when no filter", () => {
    expect(filterFloor(tables, "", false)).toHaveLength(3)
  })

  it("matches by table number or name (case-insensitive)", () => {
    expect(filterFloor(tables, "barra", false).map((t) => t.number)).toEqual([2])
    expect(filterFloor(tables, "2", false).map((t) => t.number)).toEqual([2, 12])
  })

  it("keeps only tables ready to charge (SERVED) when onlyToCharge", () => {
    expect(filterFloor(tables, "", true).map((t) => t.number)).toEqual([2])
  })
})
