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
    submitOrder: vi
      .fn()
      .mockResolvedValue({ order_id: "o1", status: "OPEN", requires_confirmation: true }),
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

  it("shows the description and a sold-out tag from the enrichment", async () => {
    const enriched: PublicMenuDTO = {
      ...MENU,
      categories: [
        {
          name: "Platos",
          items: [
            {
              id: "9",
              name: "Milanesa",
              price_amount: 850000,
              description: "Con puré",
              available_today: false,
            },
          ],
        },
      ],
    }
    renderMenu(makeApi(() => Promise.resolve(enriched)))

    expect(await screen.findByText("Milanesa")).toBeInTheDocument()
    expect(screen.getByText("Con puré")).toBeInTheDocument()
    expect(screen.getByText("Agotado")).toBeInTheDocument()
  })

  it("calls the waiter with the table token when the button is tapped", async () => {
    const api = makeApi(() => Promise.resolve(MENU))
    renderMenu(api)
    await screen.findByText("Bar Paz")

    await userEvent.click(screen.getByRole("button", { name: "Llamar al mozo" }))
    expect(api.callWaiter).toHaveBeenCalledWith("tok-123")
  })

  it("hides the cart when self-order is disabled (F1 parity)", async () => {
    renderMenu(makeApi(() => Promise.resolve(MENU))) // self_order_enabled ausente
    await screen.findByText("Bar Paz")
    // Sin steppers ni botón de envío: la carta se comporta como en F1.
    expect(screen.queryByRole("button", { name: "Sumar uno" })).not.toBeInTheDocument()
    expect(screen.queryByText(/Enviar el pedido/)).not.toBeInTheDocument()
  })

  it("builds a cart and submits the order server-side (prices never sent)", async () => {
    const api = makeApi(() =>
      Promise.resolve({ ...MENU, self_order_enabled: true, self_order_requires_confirmation: true })
    )
    renderMenu(api)
    await screen.findByText("Bar Paz")

    // Sumo 2 empanadas (la primera "+" en el DOM es la de Empanada).
    await userEvent.click(screen.getAllByRole("button", { name: "Sumar uno" })[0])
    await userEvent.click(screen.getAllByRole("button", { name: "Sumar uno" })[0]) // ahora [− 1 +]

    await userEvent.click(screen.getByRole("button", { name: /Enviar el pedido/ }))

    expect(api.submitOrder).toHaveBeenCalledWith("tok-123", [{ product_id: "1", quantity: 2 }])
    // Gate ON → mensaje "el mozo lo confirma".
    expect(await screen.findByText("¡Pedido enviado!")).toBeInTheDocument()
  })
})
