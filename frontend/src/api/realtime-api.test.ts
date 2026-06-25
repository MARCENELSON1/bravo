import { describe, expect, it, vi } from "vitest"

import type { HttpClient } from "@/api/http-client"
import { RealtimeApi } from "@/api/realtime-api"

describe("RealtimeApi", () => {
  it("requests a short-lived stream token (authenticated)", async () => {
    const request = vi.fn().mockResolvedValue({ token: "t", expires_in: 60 })
    const api = new RealtimeApi({ request } as unknown as HttpClient)

    await api.streamToken()

    const [method, path, options] = request.mock.calls[0]
    expect(method).toBe("POST")
    expect(path).toBe("/realtime/token")
    expect(options).toMatchObject({ auth: true })
  })

  it("builds the KDS stream URL with the token url-encoded", () => {
    const api = new RealtimeApi({ request: vi.fn() } as unknown as HttpClient)
    expect(api.kdsStreamUrl("a b/c")).toBe("/api/v1/realtime/kds/stream?token=a%20b%2Fc")
  })

  it("builds the floor stream URL with the token url-encoded", () => {
    const api = new RealtimeApi({ request: vi.fn() } as unknown as HttpClient)
    expect(api.floorStreamUrl("a b/c")).toBe("/api/v1/realtime/floor/stream?token=a%20b%2Fc")
  })
})
