import { describe, expect, it } from "vitest"

import type {
  FloorSessionDTO,
  FloorTableDTO,
  OrderDTO,
  SessionState,
} from "@/api/types-operations"
import { floorSummary } from "@/features/dashboard/floor-summary"

const order = (): OrderDTO => ({
  id: "o",
  table_id: "t",
  waiter_id: "w",
  status: "SENT",
  currency: "ARS",
  items: [],
  total_amount: 0,
  created_at: null,
  customer_id: null,
})

const session = (state: SessionState): FloorSessionDTO => ({
  id: "s",
  state,
  state_since: null,
  pax: null,
  waiter_id: null,
  waiter_name: null,
  sector_id: null,
})

const table = (n: number, sess: FloorSessionDTO | null): FloorTableDTO => ({
  id: `t${n}`,
  number: n,
  name: null,
  status: sess ? "OCCUPIED" : "FREE",
  active_order: sess ? order() : null,
  session: sess,
  sector_id: null,
  capacity: null,
})

describe("floorSummary", () => {
  it("cuenta libres, ocupadas, para servir y a cobrar", () => {
    const tables = [
      table(1, null),
      table(2, session("IN_KITCHEN")),
      table(3, session("TO_SERVE")),
      table(4, session("TO_CHARGE")),
      table(5, session("SERVED")),
    ]
    expect(floorSummary(tables)).toEqual({
      total: 5,
      free: 1,
      occupied: 4,
      toServe: 1,
      toCharge: 2, // TO_CHARGE + SERVED
    })
  })

  it("salón vacío → todo en cero", () => {
    expect(floorSummary([])).toEqual({
      total: 0,
      free: 0,
      occupied: 0,
      toServe: 0,
      toCharge: 0,
    })
  })
})
