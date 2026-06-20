import { describe, expect, it, vi } from "vitest"
import { screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"

import { ApiError } from "@/api/api-error"
import { LoginPage } from "@/features/identity/login-page"
import { renderWithProviders } from "@/test/test-utils"

async function fillAndSubmit() {
  const user = userEvent.setup()
  await user.type(screen.getByLabelText("Comercio"), "mi-bar")
  await user.type(screen.getByLabelText("Email"), "owner@bar.com")
  await user.type(screen.getByLabelText("Contraseña"), "secret123")
  await user.click(screen.getByRole("button", { name: /ingresar/i }))
}

describe("LoginPage", () => {
  it("shows the verify-email notice on email_not_verified (not a neutral error)", async () => {
    renderWithProviders(<LoginPage />, {
      authApi: {
        login: vi
          .fn()
          .mockRejectedValue(
            new ApiError("email_not_verified", "Tenés que verificar tu email antes de ingresar.", 403)
          ),
      },
    })
    await fillAndSubmit()
    expect(await screen.findByText(/verificar tu email/i)).toBeInTheDocument()
  })

  it("shows the Spanish message on invalid_credentials", async () => {
    renderWithProviders(<LoginPage />, {
      authApi: {
        login: vi
          .fn()
          .mockRejectedValue(
            new ApiError("invalid_credentials", "Email o contraseña incorrectos.", 401)
          ),
      },
    })
    await fillAndSubmit()
    expect(await screen.findByText("Email o contraseña incorrectos.")).toBeInTheDocument()
  })
})
