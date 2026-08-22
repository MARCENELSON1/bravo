import { describe, expect, it, vi } from "vitest"

import { FloorApi } from "@/api/floor-api"
import type { HttpClient } from "@/api/http-client"

describe("FloorApi", () => {
  it("lists the floor (authenticated)", async () => {
    const request = vi.fn().mockResolvedValue([])
    const api = new FloorApi({ request } as unknown as HttpClient)

    await api.list()

    const [method, path, options] = request.mock.calls[0]
    expect(method).toBe("GET")
    expect(path).toBe("/floor")
    expect(options).toMatchObject({ auth: true })
  })

  it("opens a session with pax", async () => {
    const request = vi.fn().mockResolvedValue({ id: "s1" })
    const api = new FloorApi({ request } as unknown as HttpClient)

    await api.openSession({ table_id: "t1", pax: 4 })

    const [method, path, options] = request.mock.calls[0]
    expect(method).toBe("POST")
    expect(path).toBe("/floor/sessions")
    expect(options).toMatchObject({ auth: true, body: { table_id: "t1", pax: 4 } })
  })

  it("requests the bill for a session", async () => {
    const request = vi.fn().mockResolvedValue({ id: "s1" })
    const api = new FloorApi({ request } as unknown as HttpClient)

    await api.requestBill("s1")

    const [method, path, options] = request.mock.calls[0]
    expect(method).toBe("POST")
    expect(path).toBe("/floor/sessions/s1/bill")
    expect(options).toMatchObject({ auth: true })
  })

  it("sets the pax for a session", async () => {
    const request = vi.fn().mockResolvedValue({ id: "s1" })
    const api = new FloorApi({ request } as unknown as HttpClient)

    await api.setPax("s1", 6)

    const [method, path, options] = request.mock.calls[0]
    expect(method).toBe("PATCH")
    expect(path).toBe("/floor/sessions/s1/pax")
    expect(options).toMatchObject({ auth: true, body: { pax: 6 } })
  })
})
