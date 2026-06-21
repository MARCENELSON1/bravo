import { describe, expect, it, vi } from "vitest"

import type { HttpClient } from "@/api/http-client"
import { IntegrationsApi } from "@/api/integrations-api"

describe("IntegrationsApi", () => {
  it("fetches the MercadoPago connection status", async () => {
    const request = vi.fn().mockResolvedValue({ connected: false })
    const api = new IntegrationsApi({ request } as unknown as HttpClient)

    await api.getMpStatus()

    const [method, path, options] = request.mock.calls[0]
    expect(method).toBe("GET")
    expect(path).toBe("/integrations/mercadopago")
    expect(options).toMatchObject({ auth: true })
  })

  it("requests the OAuth connect URL", async () => {
    const request = vi.fn().mockResolvedValue({ url: "https://auth.mercadopago.com.ar/..." })
    const api = new IntegrationsApi({ request } as unknown as HttpClient)

    await api.getMpConnectUrl()

    const [method, path] = request.mock.calls[0]
    expect(method).toBe("GET")
    expect(path).toBe("/integrations/mercadopago/connect")
  })

  it("disconnects via DELETE", async () => {
    const request = vi.fn().mockResolvedValue(undefined)
    const api = new IntegrationsApi({ request } as unknown as HttpClient)

    await api.disconnectMp()

    const [method, path] = request.mock.calls[0]
    expect(method).toBe("DELETE")
    expect(path).toBe("/integrations/mercadopago")
  })
})
