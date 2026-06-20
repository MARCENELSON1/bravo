import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { ApiError } from "@/api/api-error"
import { FetchHttpClient } from "@/api/http-client"
import {
  clearAccessToken,
  getAccessToken,
  setAccessToken,
  setUnauthorizedHandler,
} from "@/api/token-store"

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  })
}

describe("FetchHttpClient", () => {
  beforeEach(() => {
    clearAccessToken()
    setUnauthorizedHandler(null)
  })
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it("maps a non-2xx { code, message } body to an ApiError", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        jsonResponse(401, {
          code: "invalid_credentials",
          message: "Email o contraseña incorrectos.",
        })
      )
    )
    const client = new FetchHttpClient("")
    await expect(
      client.request("POST", "/auth/login", { form: new URLSearchParams() })
    ).rejects.toMatchObject({ code: "invalid_credentials", status: 401 })
  })

  it("maps a non-JSON error body to a generic ApiError", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("<html>502</html>", { status: 502 }))
    )
    const client = new FetchHttpClient("")
    await expect(client.request("GET", "/ping", { auth: true })).rejects.toBeInstanceOf(ApiError)
  })

  it("refreshes once for concurrent 401s (single-flight) and retries", async () => {
    let refreshCount = 0
    const fetchMock = vi.fn(async (url: string | URL, init?: RequestInit) => {
      if (String(url).endsWith("/auth/refresh")) {
        refreshCount += 1
        return jsonResponse(200, { access_token: "new-token" })
      }
      const headers = (init?.headers ?? {}) as Record<string, string>
      if (headers["Authorization"] === "Bearer new-token") {
        return jsonResponse(200, { ok: true })
      }
      return jsonResponse(401, { code: "expired_token", message: "expiró" })
    })
    vi.stubGlobal("fetch", fetchMock)
    setAccessToken("old-token")

    const client = new FetchHttpClient("")
    const [a, b] = await Promise.all([
      client.request<{ ok: boolean }>("GET", "/ping", { auth: true }),
      client.request<{ ok: boolean }>("GET", "/ping", { auth: true }),
    ])

    expect(a.ok).toBe(true)
    expect(b.ok).toBe(true)
    expect(refreshCount).toBe(1)
    expect(getAccessToken()).toBe("new-token")
  })

  it("tears the session down when refresh fails", async () => {
    const onUnauthorized = vi.fn()
    vi.stubGlobal(
      "fetch",
      vi.fn(async (url: string | URL) => {
        if (String(url).endsWith("/auth/refresh")) {
          return jsonResponse(401, { code: "invalid_token", message: "no" })
        }
        return jsonResponse(401, { code: "expired_token", message: "expiró" })
      })
    )
    setAccessToken("old-token")
    setUnauthorizedHandler(onUnauthorized)

    const client = new FetchHttpClient("")
    await expect(client.request("GET", "/ping", { auth: true })).rejects.toBeInstanceOf(ApiError)
    expect(onUnauthorized).toHaveBeenCalledTimes(1)
    expect(getAccessToken()).toBeNull()
  })
})
