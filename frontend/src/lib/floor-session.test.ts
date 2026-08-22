import { describe, expect, it } from "vitest"

import type {
  FloorSessionDTO,
  FloorTableDTO,
  OrderDTO,
  SessionState,
} from "@/api/types-operations"
import { floorView } from "@/lib/floor-session"

const order = (status: OrderDTO["status"], createdAt: string | null = null): OrderDTO => ({
  id: "o",
  table_id: "t",
  waiter_id: "w1",
  status,
  currency: "ARS",
  items: [],
  total_amount: 0,
  created_at: createdAt,
})

const session = (state: SessionState, since: string | null = null): FloorSessionDTO => ({
  id: "s",
  state,
  state_since: since,
  pax: 4,
  waiter_id: "w1",
  waiter_name: "Juan",
  sector_id: null,
})

const table = (ord: OrderDTO | null, sess: FloorSessionDTO | null): FloorTableDTO => ({
  id: "t1",
  number: 1,
  name: null,
  status: ord ? "OCCUPIED" : "FREE",
  active_order: ord,
  session: sess,
  sector_id: null,
  capacity: null,
})

describe("floorView", () => {
  it("free table (no order, no session)", () => {
    const v = floorView(table(null, null))
    expect(v.state).toBe("FREE")
    expect(v.label).toBe("Libre")
    expect(v.attention).toBe(false)
  })

  it("uses the session state, timer and pax when present", () => {
    const v = floorView(table(order("READY"), session("TO_SERVE", "2026-01-01T12:00:00Z")))
    expect(v.state).toBe("TO_SERVE")
    expect(v.label).toBe("Para servir ⚡")
    expect(v.since).toBe("2026-01-01T12:00:00Z")
    expect(v.attention).toBe(true)
    expect(v.pax).toBe(4)
    expect(v.waiterName).toBe("Juan")
  })

  it("a_cobrar asks for attention", () => {
    expect(floorView(table(order("SERVED"), session("TO_CHARGE"))).attention).toBe(true)
  })

  it("falls back to the order (parity) when there is no session", () => {
    const v = floorView(table(order("PREPARING", "2026-01-01T10:00:00Z"), null))
    expect(v.state).toBe("IN_KITCHEN")
    expect(v.label).toBe("En cocina")
    expect(v.since).toBe("2026-01-01T10:00:00Z")
    expect(v.pax).toBeNull()
  })
})
