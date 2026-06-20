import { beforeEach, describe, expect, it, vi } from "vitest"

import { AuthApi } from "@/api/auth-api"
import type { HttpClient } from "@/api/http-client"
import { clearAccessToken, getAccessToken } from "@/api/token-store"

describe("AuthApi.login", () => {
  beforeEach(() => clearAccessToken())

  it("sends the tenant slug as client_id and stores the access token", async () => {
    const request = vi.fn().mockResolvedValue({ access_token: "abc", token_type: "bearer" })
    const http: HttpClient = { request }
    const api = new AuthApi(http)

    await api.login("mi-bar", "owner@bar.com", "secret123")

    expect(request).toHaveBeenCalledTimes(1)
    const [method, path, options] = request.mock.calls[0]
    expect(method).toBe("POST")
    expect(path).toBe("/auth/login")
    const form = options.form as URLSearchParams
    expect(form.get("client_id")).toBe("mi-bar")
    expect(form.get("username")).toBe("owner@bar.com")
    expect(form.get("password")).toBe("secret123")
    expect(getAccessToken()).toBe("abc")
  })
})
