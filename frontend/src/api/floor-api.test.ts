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
})
