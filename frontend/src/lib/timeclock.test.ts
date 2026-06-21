import { describe, expect, it } from "vitest"

import { formatMinutes, minutesSince } from "@/lib/timeclock"

describe("formatMinutes", () => {
  it("formats minutes-only spans", () => {
    expect(formatMinutes(0)).toBe("0m")
    expect(formatMinutes(45)).toBe("45m")
  })

  it("formats whole hours", () => {
    expect(formatMinutes(480)).toBe("8h")
  })

  it("formats hours + minutes", () => {
    expect(formatMinutes(510)).toBe("8h 30m")
  })
})

describe("minutesSince", () => {
  it("counts whole minutes elapsed", () => {
    const start = "2026-06-21T09:00:00.000Z"
    const now = new Date("2026-06-21T11:30:00.000Z").getTime()
    expect(minutesSince(start, now)).toBe(150)
  })

  it("never returns a negative value", () => {
    const start = "2026-06-21T09:00:00.000Z"
    const now = new Date("2026-06-21T08:00:00.000Z").getTime()
    expect(minutesSince(start, now)).toBe(0)
  })
})
