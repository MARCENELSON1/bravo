import { describe, expect, it } from "vitest"

import { pickInitialLang } from "@/i18n"

describe("pickInitialLang", () => {
  it("respeta la elección guardada por sobre todo", () => {
    expect(pickInitialLang("es", "en-US")).toBe("es") // guardó ES aunque el navegador sea EN
    expect(pickInitialLang("en", "es-AR")).toBe("en")
  })

  it("sin elección, un navegador en inglés arranca en inglés (usuario US)", () => {
    expect(pickInitialLang(null, "en-US")).toBe("en")
    expect(pickInitialLang(null, "EN")).toBe("en")
  })

  it("sin elección, navegador español o desconocido → español (paridad)", () => {
    expect(pickInitialLang(null, "es-AR")).toBe("es")
    expect(pickInitialLang(null, "fr-FR")).toBe("es")
    expect(pickInitialLang(null, undefined)).toBe("es")
  })

  it("ignora un valor guardado inválido y cae a la detección", () => {
    expect(pickInitialLang("de", "en-US")).toBe("en")
    expect(pickInitialLang("", "es-AR")).toBe("es")
  })
})
