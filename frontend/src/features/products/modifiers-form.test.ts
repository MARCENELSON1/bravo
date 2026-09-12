import { describe, expect, it } from "vitest"

import type { ModifierGroupDTO } from "@/api/types-operations"
import {
  draftsToInput,
  groupsAreValid,
  toDrafts,
} from "@/features/products/modifiers-form"

const DTO: ModifierGroupDTO[] = [
  {
    id: "g1",
    name: "Cocción",
    min_select: 1,
    max_select: 1,
    required: true,
    options: [
      { id: "a", name: "Jugosa", price_delta: 0 },
      { id: "b", name: "Con panceta", price_delta: 300000 },
    ],
  },
]

describe("modifiers form", () => {
  it("maps a DTO to drafts (cents → pesos, 0 → empty)", () => {
    const [g] = toDrafts(DTO)
    expect(g.min).toBe("1")
    expect(g.options[0].price).toBe("") // 0 → vacío
    expect(g.options[1].price).toBe("3000") // 300000 centavos
  })

  it("maps drafts to the PUT payload (pesos → cents, drops nameless options)", () => {
    const input = draftsToInput([
      {
        name: "Cocción",
        min: "1",
        max: "1",
        options: [
          { name: "Con panceta", price: "3000" },
          { name: "", price: "999" }, // sin nombre → se descarta
        ],
      },
    ])
    expect(input).toEqual([
      {
        name: "Cocción",
        min_select: 1,
        max_select: 1,
        options: [{ name: "Con panceta", price_delta: 300000 }],
      },
    ])
  })

  it("validates group rules before hitting the API", () => {
    const ok: Parameters<typeof groupsAreValid>[0] = [
      { name: "X", min: "1", max: "1", options: [{ name: "a", price: "" }] },
    ]
    expect(groupsAreValid(ok)).toBe(true)
    // max < min
    expect(
      groupsAreValid([{ name: "X", min: "2", max: "1", options: [{ name: "a", price: "" }, { name: "b", price: "" }] }])
    ).toBe(false)
    // sin opciones con nombre
    expect(groupsAreValid([{ name: "X", min: "0", max: "1", options: [{ name: "", price: "" }] }])).toBe(
      false
    )
    // nombre de grupo vacío
    expect(groupsAreValid([{ name: "  ", min: "0", max: "1", options: [{ name: "a", price: "" }] }])).toBe(
      false
    )
  })
})
