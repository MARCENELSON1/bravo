import { describe, expect, it, vi } from "vitest"

import type { HttpClient } from "@/api/http-client"
import { ReservationsApi } from "@/api/reservations-api"

describe("ReservationsApi", () => {
  it("creates a reservation via POST with body + auth", async () => {
    const request = vi.fn().mockResolvedValue({ reservation_id: "r1" })
    const api = new ReservationsApi({ request } as unknown as HttpClient)

    await api.create({
      customer_name: "Pérez",
      party_size: 2,
      reserved_at: "2026-06-21T21:00:00.000Z",
      turn: "DINNER",
    })

    const [method, path, options] = request.mock.calls[0]
    expect(method).toBe("POST")
    expect(path).toBe("/reservations")
    expect(options).toMatchObject({ auth: true, body: { customer_name: "Pérez", turn: "DINNER" } })
  })

  it("builds the agenda query string from day + turn", async () => {
    const request = vi.fn().mockResolvedValue([])
    const api = new ReservationsApi({ request } as unknown as HttpClient)

    await api.list({ from: "2026-06-21T00:00:00.000Z", to: "2026-06-21T23:59:59.000Z", turn: "DINNER" })

    const [method, path] = request.mock.calls[0]
    expect(method).toBe("GET")
    expect(path).toContain("/reservations?")
    expect(path).toContain("from=2026-06-21")
    expect(path).toContain("turn=DINNER")
  })

  it("omits the query string when no filters are given", async () => {
    const request = vi.fn().mockResolvedValue([])
    const api = new ReservationsApi({ request } as unknown as HttpClient)

    await api.list()

    expect(request.mock.calls[0][1]).toBe("/reservations")
  })

  it("confirms via POST to the confirm endpoint", async () => {
    const request = vi.fn().mockResolvedValue({ id: "r1", status: "CONFIRMED" })
    const api = new ReservationsApi({ request } as unknown as HttpClient)

    await api.confirm("r1")

    const [method, path, options] = request.mock.calls[0]
    expect(method).toBe("POST")
    expect(path).toBe("/reservations/r1/confirm")
    expect(options).toMatchObject({ auth: true })
  })

  it("marks no-show via the hyphenated endpoint", async () => {
    const request = vi.fn().mockResolvedValue({ id: "r1", status: "NO_SHOW" })
    const api = new ReservationsApi({ request } as unknown as HttpClient)

    await api.noShow("r1")

    expect(request.mock.calls[0][1]).toBe("/reservations/r1/no-show")
  })

  it("reschedules via PATCH with the new data", async () => {
    const request = vi.fn().mockResolvedValue({ id: "r1", party_size: 4 })
    const api = new ReservationsApi({ request } as unknown as HttpClient)

    await api.update("r1", {
      party_size: 4,
      reserved_at: "2026-06-22T13:00:00.000Z",
      turn: "LUNCH",
    })

    const [method, path, options] = request.mock.calls[0]
    expect(method).toBe("PATCH")
    expect(path).toBe("/reservations/r1")
    expect(options.body).toMatchObject({ party_size: 4, turn: "LUNCH" })
  })
})
