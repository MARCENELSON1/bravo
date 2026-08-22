import { describe, expect, it, vi } from "vitest"

import type { HttpClient } from "@/api/http-client"
import { SectorsApi } from "@/api/sectors-api"

describe("SectorsApi", () => {
  it("lists sectors (authenticated)", async () => {
    const request = vi.fn().mockResolvedValue([])
    await new SectorsApi({ request } as unknown as HttpClient).list()
    const [method, path, options] = request.mock.calls[0]
    expect(method).toBe("GET")
    expect(path).toBe("/sectors")
    expect(options).toMatchObject({ auth: true })
  })

  it("creates a sector", async () => {
    const request = vi.fn().mockResolvedValue({ id: "s1" })
    await new SectorsApi({ request } as unknown as HttpClient).create({
      name: "Terraza",
      color: "#0af",
      sort_order: 1,
    })
    const [method, path, options] = request.mock.calls[0]
    expect(method).toBe("POST")
    expect(path).toBe("/sectors")
    expect(options).toMatchObject({ auth: true, body: { name: "Terraza", color: "#0af", sort_order: 1 } })
  })

  it("updates a sector (PUT)", async () => {
    const request = vi.fn().mockResolvedValue({ id: "s1" })
    await new SectorsApi({ request } as unknown as HttpClient).update("s1", { name: "Salón" })
    const [method, path] = request.mock.calls[0]
    expect(method).toBe("PUT")
    expect(path).toBe("/sectors/s1")
  })

  it("deletes a sector", async () => {
    const request = vi.fn().mockResolvedValue(undefined)
    await new SectorsApi({ request } as unknown as HttpClient).remove("s1")
    const [method, path] = request.mock.calls[0]
    expect(method).toBe("DELETE")
    expect(path).toBe("/sectors/s1")
  })
})
