import { describe, expect, it } from "vitest"

import { splitCategory } from "@/lib/menu-tree"

describe("splitCategory", () => {
  it("separa categoría y subcategoría", () => {
    expect(splitCategory("Bebidas / Cervezas")).toEqual({ main: "Bebidas", sub: "Cervezas" })
  })

  it("tolera el separador sin espacios", () => {
    expect(splitCategory("Bebidas/Cervezas")).toEqual({ main: "Bebidas", sub: "Cervezas" })
  })

  it("sin separador, solo hay categoría", () => {
    expect(splitCategory("Postres")).toEqual({ main: "Postres", sub: null })
  })

  it("corta en el primer separador y deja el resto como nombre", () => {
    expect(splitCategory("Bebidas / Cervezas / IPA")).toEqual({
      main: "Bebidas",
      sub: "Cervezas / IPA",
    })
  })

  it("sin categoría, no hay niveles", () => {
    expect(splitCategory(null)).toEqual({ main: null, sub: null })
    expect(splitCategory("")).toEqual({ main: null, sub: null })
    expect(splitCategory("   ")).toEqual({ main: null, sub: null })
  })

  it("mal cargado: usa lo que haya como nivel 1", () => {
    expect(splitCategory("/ Cervezas")).toEqual({ main: "Cervezas", sub: null })
    expect(splitCategory("Bebidas /")).toEqual({ main: "Bebidas", sub: null })
  })
})
