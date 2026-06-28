import { describe, expect, it } from "vitest"

import type { ProductDTO } from "@/api/types-operations"
import { rankProducts } from "@/lib/product-usage"

const product = (id: string, name: string, extra: Partial<ProductDTO> = {}): ProductDTO => ({
  id,
  name,
  price_amount: 1000,
  currency: "ARS",
  category: null,
  station: "KITCHEN",
  active: true,
  ...extra,
})

describe("rankProducts", () => {
  const products = [
    product("1", "Milanesa"),
    product("2", "Lomo", { category: "Carnes" }),
    product("3", "Agua", { active: false }),
  ]

  it("excludes inactive and sorts active alphabetically by default", () => {
    expect(rankProducts(products, "", {}).map((p) => p.id)).toEqual(["2", "1"])
  })

  it("filters by name or category, case-insensitive", () => {
    expect(rankProducts(products, "LO", {}).map((p) => p.id)).toEqual(["2"])
    expect(rankProducts(products, "carne", {}).map((p) => p.id)).toEqual(["2"])
  })

  it("floats most-used products to the top", () => {
    expect(rankProducts(products, "", { "1": 5 }).map((p) => p.id)).toEqual(["1", "2"])
  })
})
