import { afterEach, describe, expect, it } from "vitest"
import { screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"

import { LoginPage } from "@/features/identity/login-page"
import { setLanguage } from "@/i18n"
import { renderWithProviders } from "@/test/test-utils"

describe("LanguageSwitcher", () => {
  afterEach(() => setLanguage("es")) // no contaminar el idioma global entre tests

  it("switches the login page between Spanish and English", async () => {
    const user = userEvent.setup()
    renderWithProviders(<LoginPage />)

    // Arranca en español (default → paridad).
    expect(screen.getByRole("button", { name: /ingresar/i })).toBeInTheDocument()

    // Pasar a English cambia los textos migrados.
    await user.click(screen.getByRole("button", { name: "EN" }))
    expect(await screen.findByRole("button", { name: /sign in/i })).toBeInTheDocument()
    expect(screen.getByLabelText("Business")).toBeInTheDocument()

    // Volver a español.
    await user.click(screen.getByRole("button", { name: "ES" }))
    expect(await screen.findByLabelText("Comercio")).toBeInTheDocument()
  })
})
