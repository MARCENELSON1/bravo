import { describe, expect, it } from "vitest"

import type { Course, ItemStatus, OrderDTO, OrderItemDTO } from "@/api/types-operations"
import {
  courseOf,
  courseState,
  coursesOf,
  heldCount,
  nextHeldCourse,
  readyCourse,
} from "@/lib/courses"

const item = (
  id: string,
  status: ItemStatus,
  course?: Course
): OrderItemDTO => ({
  id,
  product_id: `p-${id}`,
  name: id,
  unit_price_amount: 1000,
  quantity: 1,
  note: null,
  status,
  station: "KITCHEN",
  ...(course ? { course } : {}),
  sent_at: null,
})

const order = (items: OrderItemDTO[], over: Partial<OrderDTO> = {}): OrderDTO => ({
  id: "o1",
  table_id: "t1",
  waiter_id: "w1",
  status: "SENT",
  currency: "ARS",
  items,
  total_amount: 0,
  source: "WAITER",
  created_at: null,
  customer_id: null,
  ...over,
})

describe("courseOf", () => {
  it("cae a MAIN cuando la línea no trae curso (paridad con lo viejo)", () => {
    expect(courseOf(item("a", "PENDING"))).toBe("MAIN")
    expect(courseOf(item("b", "PENDING", "STARTER"))).toBe("STARTER")
  })
})

describe("coursesOf", () => {
  it("devuelve los presentes en orden de servicio, sin los anulados", () => {
    const items = [
      item("flan", "PENDING", "DESSERT"),
      item("agua", "SENT", "IMMEDIATE"),
      item("bife", "HELD", "MAIN"),
      item("prov", "SENT", "STARTER"),
      item("x", "CANCELLED", "MAIN"),
    ]
    expect(coursesOf(items)).toEqual(["IMMEDIATE", "STARTER", "MAIN", "DESSERT"])
  })
})

describe("courseState", () => {
  it("cocinando gana sobre listo (un plato del tiempo sigue al fuego)", () => {
    const items = [
      item("a", "READY", "STARTER"),
      item("b", "PREPARING", "STARTER"),
    ]
    expect(courseState(items, "STARTER")).toBe("IN_KITCHEN")
  })

  it("listo cuando todos los del tiempo están listos", () => {
    const items = [item("a", "READY", "STARTER"), item("b", "READY", "STARTER")]
    expect(courseState(items, "STARTER")).toBe("READY")
  })

  it("en espera, sin marchar y servido", () => {
    expect(courseState([item("a", "HELD", "MAIN")], "MAIN")).toBe("HELD")
    expect(courseState([item("a", "PENDING", "MAIN")], "MAIN")).toBe("PENDING")
    expect(courseState([item("a", "SERVED", "MAIN")], "MAIN")).toBe("SERVED")
  })

  it("null cuando ese tiempo no tiene platos", () => {
    expect(courseState([item("a", "SENT", "MAIN")], "DESSERT")).toBeNull()
  })

  it("ignora los anulados", () => {
    const items = [item("a", "CANCELLED", "STARTER"), item("b", "READY", "STARTER")]
    expect(courseState(items, "STARTER")).toBe("READY")
  })
})

describe("readyCourse", () => {
  it("devuelve el curso más bajo que está listo (la entrada antes que el principal)", () => {
    const o = order([
      item("bife", "READY", "MAIN"),
      item("prov", "READY", "STARTER"),
    ])
    expect(readyCourse(o)).toBe("STARTER")
  })

  it("null si no hay nada listo", () => {
    const o = order([item("prov", "SERVED", "STARTER"), item("bife", "SENT", "MAIN")])
    expect(readyCourse(o)).toBeNull()
  })

  it("regresión: entrada servida + bebida en cocina → nada para servir", () => {
    const o = order([
      item("burrata", "SERVED", "STARTER"),
      item("empanadas", "SERVED", "STARTER"),
      item("aperol", "SENT", "IMMEDIATE"),
    ])
    expect(readyCourse(o)).toBeNull()
  })
})

describe("heldCount / nextHeldCourse", () => {
  it("cuenta lo que espera y devuelve el próximo tiempo a marchar", () => {
    const o = order([
      item("prov", "SENT", "STARTER"),
      item("bife", "HELD", "MAIN"),
      item("flan", "HELD", "DESSERT"),
    ])
    expect(heldCount(o)).toBe(2)
    expect(nextHeldCourse(o)).toBe("MAIN")
  })

  it("prefiere el derivado del server cuando viene", () => {
    const o = order([item("bife", "HELD", "MAIN")], { next_course: "DESSERT" })
    expect(nextHeldCourse(o)).toBe("DESSERT")
  })

  it("null cuando no hay nada en espera", () => {
    expect(nextHeldCourse(order([item("a", "SENT", "MAIN")]))).toBeNull()
  })
})
