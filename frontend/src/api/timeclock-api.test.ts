import { describe, expect, it, vi } from "vitest"

import type { HttpClient } from "@/api/http-client"
import { TimeClockApi } from "@/api/timeclock-api"

describe("TimeClockApi", () => {
  it("toggles the shift via POST /timeclock/punch", async () => {
    const request = vi.fn().mockResolvedValue({ id: "s1", status: "OPEN" })
    const api = new TimeClockApi({ request } as unknown as HttpClient)

    await api.punch()

    const [method, path, options] = request.mock.calls[0]
    expect(method).toBe("POST")
    expect(path).toBe("/timeclock/punch")
    expect(options).toMatchObject({ auth: true })
  })

  it("builds the shifts query string from user_id + period", async () => {
    const request = vi.fn().mockResolvedValue([])
    const api = new TimeClockApi({ request } as unknown as HttpClient)

    await api.listShifts({ userId: "u1", from: "2026-06-01T00:00:00.000Z", to: "2026-06-30T23:59:59.000Z" })

    const [method, path] = request.mock.calls[0]
    expect(method).toBe("GET")
    expect(path).toContain("/timeclock/shifts?")
    expect(path).toContain("user_id=u1")
    expect(path).toContain("from=2026-06-01")
    expect(path).toContain("to=2026-06-30")
  })

  it("omits the query string when no filters are given", async () => {
    const request = vi.fn().mockResolvedValue([])
    const api = new TimeClockApi({ request } as unknown as HttpClient)

    await api.listShifts()

    expect(request.mock.calls[0][1]).toBe("/timeclock/shifts")
  })

  it("adjusts a shift via PATCH with the new times", async () => {
    const request = vi.fn().mockResolvedValue({ id: "s1", source: "MANAGER" })
    const api = new TimeClockApi({ request } as unknown as HttpClient)

    await api.adjustShift("s1", {
      clock_in_at: "2026-06-21T09:00:00.000Z",
      clock_out_at: "2026-06-21T17:00:00.000Z",
    })

    const [method, path, options] = request.mock.calls[0]
    expect(method).toBe("PATCH")
    expect(path).toBe("/timeclock/shifts/s1")
    expect(options.body).toMatchObject({ clock_out_at: "2026-06-21T17:00:00.000Z" })
  })

  it("requests the staff report with the period", async () => {
    const request = vi.fn().mockResolvedValue({ currency: "ARS", rows: [] })
    const api = new TimeClockApi({ request } as unknown as HttpClient)

    await api.staffReport({ from: "2026-06-01T00:00:00.000Z" })

    const [method, path] = request.mock.calls[0]
    expect(method).toBe("GET")
    expect(path).toContain("/reports/staff?")
    expect(path).toContain("from=2026-06-01")
  })

  it("registers a presence device", async () => {
    const request = vi.fn().mockResolvedValue({ device_token: "dev.tok" })
    const api = new TimeClockApi({ request } as unknown as HttpClient)

    await api.registerPresenceDevice()

    const [method, path, options] = request.mock.calls[0]
    expect(method).toBe("POST")
    expect(path).toBe("/timeclock/presence/devices")
    expect(options).toMatchObject({ auth: true })
  })

  it("fetches the challenge with the device token header (no user auth)", async () => {
    const request = vi.fn().mockResolvedValue({ qr_payload: "1.ab", code: "ABCDEF" })
    const api = new TimeClockApi({ request } as unknown as HttpClient)

    await api.presenceChallenge("dev.tok")

    const [method, path, options] = request.mock.calls[0]
    expect(method).toBe("GET")
    expect(path).toBe("/timeclock/presence/current")
    expect(options.headers).toMatchObject({ "X-Device-Token": "dev.tok" })
    expect(options.auth).toBeUndefined()
  })

  it("punches by presenting a token", async () => {
    const request = vi.fn().mockResolvedValue({ id: "s1", source: "PRESENCE" })
    const api = new TimeClockApi({ request } as unknown as HttpClient)

    await api.presencePunch("ABCDEF")

    const [method, path, options] = request.mock.calls[0]
    expect(method).toBe("POST")
    expect(path).toBe("/timeclock/presence/punch")
    expect(options).toMatchObject({ body: { presented: "ABCDEF" }, auth: true })
  })
})
