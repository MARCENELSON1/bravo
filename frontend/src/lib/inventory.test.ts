import { beforeAll, describe, expect, it } from "vitest"

import i18n from "@/i18n"
import { formatBps, formatQty, toMilesimas } from "@/lib/inventory"

// formatQty/formatBps siguen el idioma activo (numberLocale). Fijamos español
// para asertar el formato es-AR ("1,5", "10,7%") de forma determinista.
beforeAll(async () => {
  await i18n.changeLanguage("es")
})

describe("inventory formatting", () => {
  it("formats milésimas into a human quantity with the unit label", () => {
    expect(formatQty(1500, "KG")).toBe("1,5 kg")
    expect(formatQty(200, "G")).toBe("0,2 g")
    expect(formatQty(1000, "UNIT")).toBe("1 u")
  })

  it("shows negative stock as-is (oversold)", () => {
    expect(formatQty(-300, "KG")).toBe("-0,3 kg")
  })

  it("converts a typed decimal quantity into milésimas", () => {
    expect(toMilesimas("1.5")).toBe(1500)
    expect(toMilesimas("0.2")).toBe(200)
    expect(toMilesimas("3")).toBe(3000)
  })

  it("formats a basis-points food cost ratio as a percent", () => {
    expect(formatBps(3300)).toBe("33%")
    expect(formatBps(1067)).toBe("10,7%")
  })
})
