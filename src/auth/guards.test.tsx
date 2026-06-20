import { describe, expect, it, vi } from "vitest"
import { Route, Routes } from "react-router-dom"
import { screen } from "@testing-library/react"

import { RequireAuth } from "@/auth/require-auth"
import { RequireRole } from "@/auth/require-role"
import { renderWithProviders } from "@/test/test-utils"

describe("route guards", () => {
  it("redirects an anonymous user to /login", async () => {
    renderWithProviders(
      <Routes>
        <Route element={<RequireAuth />}>
          <Route path="/app" element={<div>contenido protegido</div>} />
        </Route>
        <Route path="/login" element={<div>pantalla de login</div>} />
      </Routes>,
      { route: "/app" }
    )
    expect(await screen.findByText("pantalla de login")).toBeInTheDocument()
  })

  it("blocks a role that is not in the allow list", async () => {
    renderWithProviders(
      <Routes>
        <Route element={<RequireAuth />}>
          <Route element={<RequireRole allow={["OWNER", "MANAGER"]} />}>
            <Route path="/app/invite" element={<div>pantalla de invitar</div>} />
          </Route>
        </Route>
        <Route path="/login" element={<div>login</div>} />
      </Routes>,
      {
        route: "/app/invite",
        authApi: {
          refresh: vi.fn().mockResolvedValue(undefined),
          me: vi.fn().mockResolvedValue({ tenant_id: "t1", user_id: "u1", role: "WAITER" }),
        },
      }
    )
    expect(await screen.findByText(/no tenés permisos/i)).toBeInTheDocument()
  })
})
