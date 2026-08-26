import { beforeAll, describe, expect, it } from "vitest"

import i18n from "@/i18n"
import { BUCKET_LABELS, BUCKET_ORDER, formatPct, SEVERITY_VARIANT } from "@/lib/advisor"

// formatPct sigue el idioma activo (numberLocale). Fijamos español para asertar
// el formato es-AR ("10,7%") de forma determinista.
beforeAll(async () => {
  await i18n.changeLanguage("es")
})

describe("advisor helpers", () => {
  it("orders and labels the buckets (Actuá hoy → Bien hecho)", () => {
    expect(BUCKET_ORDER[0]).toBe("TODAY")
    expect(BUCKET_LABELS.TODAY).toBe("Actuá hoy")
    expect(BUCKET_LABELS.WELL_DONE).toBe("Bien hecho")
  })

  it("maps severity to a badge variant", () => {
    expect(SEVERITY_VARIANT.CRITICAL).toBe("destructive")
    expect(SEVERITY_VARIANT.GOOD).toBe("default")
  })

  it("formats basis points as a percent", () => {
    expect(formatPct(3300)).toBe("33%")
    expect(formatPct(1067)).toBe("10,7%")
  })
})
