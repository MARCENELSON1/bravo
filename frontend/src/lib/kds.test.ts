import { describe, expect, it } from "vitest"

import { kdsDelay } from "@/lib/kds"

describe("kdsDelay", () => {
  const base = Date.parse("2026-06-24T20:00:00Z")

  it("is fresh under 5 minutes", () => {
    const d = kdsDelay("2026-06-24T19:58:00Z", base)
    expect(d.minutes).toBe(2)
    expect(d.level).toBe("fresh")
  })

  it("warns between 5 and 10 minutes", () => {
    expect(kdsDelay("2026-06-24T19:53:00Z", base).level).toBe("warn")
  })

  it("is late at 10+ minutes", () => {
    expect(kdsDelay("2026-06-24T19:49:00Z", base).level).toBe("late")
  })

  it("is safe with null or invalid timestamps", () => {
    expect(kdsDelay(null, base)).toEqual({ minutes: 0, level: "fresh" })
    expect(kdsDelay("not-a-date", base)).toEqual({ minutes: 0, level: "fresh" })
  })
})
