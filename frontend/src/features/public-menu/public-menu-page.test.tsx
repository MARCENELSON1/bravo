import { describe, expect, it, vi } from "vitest"
import { screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { Route, Routes } from "react-router-dom"

import { ApiError } from "@/api/api-error"
import type { PublicMenuApi, PublicMenuDTO } from "@/api/public-menu-api"
import { PublicMenuPage } from "@/features/public-menu/public-menu-page"
import type { Services } from "@/services/services-context"
import { renderWithProviders } from "@/test/test-utils"

function makeApi(getMenu: () => Promise<PublicMenuDTO>) {
  return {
    getMenu: vi.fn(getMenu),
    callWaiter: vi.fn().mockResolvedValue(undefined),
    requestBill: vi.fn().mockResolvedValue(undefined),
  } as unknown as PublicMenuApi
}

function renderMenu(publicMenuApi: PublicMenuApi) {
  return renderWithProviders(
    <Routes>
      <Route path="/carta/:token" element={<PublicMenuPage />} />
    </Routes>,
    { route: "/carta/tok-123", services: { publicMenuApi } as Partial<Services> }
  )
}

const MENU: PublicMenuDTO = {
  tenant_name: "Bar Paz",
  currency: "ARS",
  locale: "es-AR",
  categories: [
    {
      name: "Entradas",
      items: [
        { id: "1", name: "Empanada", price_amount: 150000 },
        { id: "2", name: "Provoleta", price_amount: 400000 },
      ],
    },
    { name: "Platos", items: [{ id: "3", name: "Pizza", price_amount: 1200000 }] },
  ],
}

describe("PublicMenuPage", () => {
  it("renders the branded menu with categories, items and prices", async () => {
    renderMenu(makeApi(() => Promise.resolve(MENU)))

    expect(await screen.findByText("Bar Paz")).toBeInTheDocument()
    expect(screen.getByText("Entradas")).toBeInTheDocument()
    expect(screen.getByText("Empanada")).toBeInTheDocument()
    expect(screen.getByText("Pizza")).toBeInTheDocument()
    // ARS formatting (es-AR): $1.500,00 for 150000 minor units.
    expect(screen.getByText(/1\.500/)).toBeInTheDocument()
  })

  it("shows the friendly invalid-token screen on invalid_table_qr_token", async () => {
    renderMenu(
      makeApi(() =>
        Promise.reject(new ApiError("invalid_table_qr_token", "El código QR no es válido.", 401))
      )
    )
    expect(await screen.findByText("No pudimos abrir la carta")).toBeInTheDocument()
  })

  it("shows the empty state when there are no items", async () => {
    renderMenu(makeApi(() => Promise.resolve({ ...MENU, categories: [{ name: "Vacía", items: [] }] })))
    expect(await screen.findByText("Carta en preparación")).toBeInTheDocument()
  })

  it("calls the waiter with the table token when the button is tapped", async () => {
    const api = makeApi(() => Promise.resolve(MENU))
    renderMenu(api)
    await screen.findByText("Bar Paz")

    await userEvent.click(screen.getByRole("button", { name: "Llamar al mozo" }))
    expect(api.callWaiter).toHaveBeenCalledWith("tok-123")
  })
})
