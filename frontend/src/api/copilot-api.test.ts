import { describe, expect, it, vi } from "vitest"

import { CopilotApi } from "@/api/copilot-api"
import type { HttpClient } from "@/api/http-client"

describe("CopilotApi", () => {
  it("asks via POST with the question + auth", async () => {
    const request = vi.fn().mockResolvedValue({ answer: "...", sql: "SELECT 1", columns: [], rows: [] })
    const api = new CopilotApi({ request } as unknown as HttpClient)

    await api.ask("¿cuánto vendí?")

    const [method, path, options] = request.mock.calls[0]
    expect(method).toBe("POST")
    expect(path).toBe("/copilot/ask")
    expect(options).toMatchObject({ auth: true, body: { question: "¿cuánto vendí?" } })
  })
})
