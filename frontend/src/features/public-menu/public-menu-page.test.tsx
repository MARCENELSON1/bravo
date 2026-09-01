import { describe, expect, it, vi } from "vitest"
import { screen } from "@testing-library/react"
import { Route, Routes } from "react-router-dom"

import { ApiError } from "@/api/api-error"
import type { PublicMenuApi, PublicMenuDTO } from "@/api/public-menu-api"
import { PublicMenuPage } from "@/features/public-menu/public-menu-page"
import type { Services } from "@/services/services-context"
import { renderWithProviders } from "@/test/test-utils"

function renderMenu(getMenu: () => Promise<PublicMenuDTO>) {
  const publicMenuApi = { getMenu: vi.fn(getMenu) } as unknown as PublicMenuApi
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
    renderMenu(() => Promise.resolve(MENU))

    expect(await screen.findByText("Bar Paz")).toBeInTheDocument()
    expect(screen.getByText("Entradas")).toBeInTheDocument()
    expect(screen.getByText("Empanada")).toBeInTheDocument()
    expect(screen.getByText("Pizza")).toBeInTheDocument()
    // ARS formatting (es-AR): $1.500,00 for 150000 minor units.
    expect(screen.getByText(/1\.500/)).toBeInTheDocument()
  })

  it("shows the friendly invalid-token screen on invalid_table_qr_token", async () => {
    renderMenu(() =>
      Promise.reject(new ApiError("invalid_table_qr_token", "El código QR no es válido.", 401))
    )
    expect(await screen.findByText("No pudimos abrir la carta")).toBeInTheDocument()
  })

  it("shows the empty state when there are no items", async () => {
    renderMenu(() =>
      Promise.resolve({ ...MENU, categories: [{ name: "Vacía", items: [] }] })
    )
    expect(await screen.findByText("Carta en preparación")).toBeInTheDocument()
  })
})
