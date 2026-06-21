import { describe, expect, it } from "vitest"

import {
  RESERVATION_STATUS_LABELS,
  RESERVATION_STATUS_VARIANT,
  SERVICE_TURN_LABELS,
  toReservedAtIso,
} from "@/lib/reservations"

describe("reservations helpers", () => {
  it("labels every status and turn in Spanish", () => {
    expect(RESERVATION_STATUS_LABELS.NO_SHOW).toBe("No-show")
    expect(RESERVATION_STATUS_LABELS.SEATED).toBe("Sentada")
    expect(SERVICE_TURN_LABELS.LUNCH).toBe("Almuerzo")
    expect(SERVICE_TURN_LABELS.DINNER).toBe("Cena")
  })

  it("maps terminal-cancel states to a destructive badge", () => {
    expect(RESERVATION_STATUS_VARIANT.CANCELLED).toBe("destructive")
    expect(RESERVATION_STATUS_VARIANT.NO_SHOW).toBe("destructive")
    expect(RESERVATION_STATUS_VARIANT.CONFIRMED).toBe("default")
  })

  it("combines a date + time into an ISO instant", () => {
    const iso = toReservedAtIso("2026-06-21", "21:00")
    // Round-trips back to the same wall-clock time in local tz.
    const d = new Date(iso)
    expect(d.getHours()).toBe(21)
    expect(d.getMinutes()).toBe(0)
  })
})
