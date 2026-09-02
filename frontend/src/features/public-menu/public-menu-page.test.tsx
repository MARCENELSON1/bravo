import { beforeEach, describe, expect, it, vi } from "vitest"
import { screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { Route, Routes } from "react-router-dom"

import { ApiError } from "@/api/api-error"
import type { PublicMenuApi, PublicMenuDTO, TableBillDTO } from "@/api/public-menu-api"
import { PublicMenuPage } from "@/features/public-menu/public-menu-page"
import type { Services } from "@/services/services-context"
import { renderWithProviders } from "@/test/test-utils"

const EMPTY_BILL: TableBillDTO = {
  currency: "ARS",
  items: [],
  total: 0,
  paid: 0,
  balance: 0,
  online_pay_available: false,
  tips_enabled: true,
}

function makeApi(getMenu: () => Promise<PublicMenuDTO>, bill: TableBillDTO = EMPTY_BILL) {
  return {
    getMenu: vi.fn(getMenu),
    callWaiter: vi.fn().mockResolvedValue(undefined),
    requestBill: vi.fn().mockResolvedValue(undefined),
    submitOrder: vi
      .fn()
      .mockResolvedValue({ order_id: "o1", status: "OPEN", requires_confirmation: true }),
    bill: vi.fn().mockResolvedValue(bill),
    pay: vi.fn().mockResolvedValue({
      payment_id: "pay-1",
      order_id: "o1",
      status: "CONFIRMED",
      amount: bill.balance,
      tip: 0,
      checkout_url: null,
    }),
    paymentStatus: vi.fn().mockResolvedValue({
      payment_id: "pay-1",
      status: "CONFIRMED",
      amount: bill.balance,
      tip: 0,
    }),
    receipt: vi.fn().mockResolvedValue({
      venue_name: "Bar Paz",
      currency: "ARS",
      items: bill.items,
      amount: bill.balance,
      tip: 0,
      method: "MERCADOPAGO",
      paid_at: "2026-09-01T20:00:00Z",
    }),
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
  // El pago iniciado se recuerda en sessionStorage por mesa → aislamos entre tests.
  beforeEach(() => {
    try {
      sessionStorage.clear()
    } catch {
      /* storage no disponible en el entorno de test */
    }
  })

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
    // Sin steppers ni botón de pedido: la carta se comporta como en F1.
    expect(screen.queryByRole("button", { name: "Sumar uno" })).not.toBeInTheDocument()
    expect(screen.queryByText(/Ver pedido/)).not.toBeInTheDocument()
  })

  it("builds a cart and submits the order server-side (prices never sent)", async () => {
    const api = makeApi(() =>
      Promise.resolve({ ...MENU, self_order_enabled: true, self_order_requires_confirmation: true })
    )
    renderMenu(api)
    await screen.findByText("Bar Paz")

    // Sumo 2 empanadas (la primera "+" en el DOM es la de Empanada).
    await userEvent.click(screen.getAllByRole("button", { name: "Sumar uno" })[0])
    await userEvent.click(screen.getAllByRole("button", { name: "Sumar uno" })[0]) // [− 1 +]

    // Abro la revisión del pedido y envío.
    await userEvent.click(screen.getByRole("button", { name: /Ver pedido/ }))
    await userEvent.click(screen.getByRole("button", { name: "Enviar el pedido" }))

    expect(api.submitOrder).toHaveBeenCalledWith("tok-123", [{ product_id: "1", quantity: 2 }])
    // Gate ON → mensaje "el mozo lo confirma".
    expect(await screen.findByText("¡Pedido enviado!")).toBeInTheDocument()
  })

  it("picks a modifier and sends the chosen option id (min/max gated)", async () => {
    const withMods: PublicMenuDTO = {
      ...MENU,
      self_order_enabled: true,
      self_order_requires_confirmation: false,
      categories: [
        {
          name: "Platos",
          items: [
            {
              id: "9",
              name: "Bife",
              price_amount: 1200000,
              modifier_groups: [
                {
                  id: "g1",
                  name: "Cocción",
                  min_select: 1,
                  max_select: 1,
                  required: true,
                  options: [
                    { id: "rare", name: "Jugosa", price_delta: 0 },
                    { id: "bacon", name: "Con panceta", price_delta: 300000 },
                  ],
                },
              ],
            },
          ],
        },
      ],
    }
    const api = makeApi(() => Promise.resolve(withMods))
    renderMenu(api)
    await screen.findByText("Bife")

    // Ítem con modificadores → "Agregar" abre el picker.
    await userEvent.click(screen.getByRole("button", { name: /Agregar/ }))
    await userEvent.click(await screen.findByLabelText(/Con panceta/))
    await userEvent.click(screen.getByRole("button", { name: "Agregar al pedido" }))

    await userEvent.click(screen.getByRole("button", { name: /Ver pedido/ }))
    await userEvent.click(screen.getByRole("button", { name: "Enviar el pedido" }))

    expect(api.submitOrder).toHaveBeenCalledWith("tok-123", [
      { product_id: "9", quantity: 1, option_ids: ["bacon"] },
    ])
  })

  it("keeps 'Pedir la cuenta' when online pay is unavailable (F1 fallback)", async () => {
    renderMenu(makeApi(() => Promise.resolve(MENU))) // EMPTY_BILL → online_pay_available false
    expect(await screen.findByRole("button", { name: "Pedir la cuenta" })).toBeInTheDocument()
    expect(screen.queryByRole("button", { name: "Pagar" })).not.toBeInTheDocument()
  })

  it("offers 'Pagar' and settles the bill via the pay endpoint", async () => {
    const bill: TableBillDTO = {
      currency: "ARS",
      items: [{ name: "Pizza", quantity: 2, unit_price: 1200000 }],
      total: 2400000,
      paid: 0,
      balance: 2400000,
      online_pay_available: true,
      tips_enabled: false,
    }
    const api = makeApi(() => Promise.resolve(MENU), bill)
    renderMenu(api)

    // Con pago online disponible, "Pagar" reemplaza "Pedir la cuenta".
    await userEvent.click(await screen.findByRole("button", { name: "Pagar" }))
    expect(screen.queryByRole("button", { name: "Pedir la cuenta" })).not.toBeInTheDocument()

    // La hoja muestra el saldo y el botón "Pagar $24.000,00" (server-side).
    await userEvent.click(await screen.findByRole("button", { name: /Pagar.*24/ }))
    // "Pagar todo" (default) → amount null; el server cobra el saldo vigente.
    expect(api.pay).toHaveBeenCalledWith("tok-123", 0, null, expect.any(String))

    // Confirma (gateway sin checkout_url) → pantalla de pagado con el recibo.
    expect(await screen.findByText("¡Pagado! 🎉")).toBeInTheDocument()
    expect(await screen.findByText("Comprobante no fiscal")).toBeInTheDocument()
    expect(screen.getByText("Pagaste")).toBeInTheDocument()
    expect(api.receipt).toHaveBeenCalledWith("tok-123", "pay-1")
  })

  it("splits the bill and pays only my share", async () => {
    const bill: TableBillDTO = {
      currency: "ARS",
      items: [{ name: "Pizza", quantity: 2, unit_price: 1200000 }],
      total: 2400000,
      paid: 0,
      balance: 2400000,
      online_pay_available: true,
      tips_enabled: false,
    }
    const api = makeApi(() => Promise.resolve(MENU), bill)
    renderMenu(api)

    await userEvent.click(await screen.findByRole("button", { name: "Pagar" }))
    // Dividir → "Mi parte": por default entre 2 → 1.200.000 (la mitad).
    await userEvent.click(await screen.findByRole("button", { name: "Mi parte" }))
    await userEvent.click(screen.getByRole("button", { name: /Pagar.*12/ }))

    expect(api.pay).toHaveBeenCalledWith("tok-123", 0, 1200000, expect.any(String))
  })

  it("resumes the payment when returning from MercadoPago (external_reference)", async () => {
    const api = makeApi(() => Promise.resolve(MENU))
    renderWithProviders(
      <Routes>
        <Route path="/carta/:token" element={<PublicMenuPage />} />
      </Routes>,
      {
        route: "/carta/tok-123?external_reference=t1:pay-1&status=approved",
        services: { publicMenuApi: api } as Partial<Services>,
      }
    )

    // Sin sessionStorage: el pago se retoma del external_reference que agrega MP.
    expect(await screen.findByText("¡Pagado! 🎉")).toBeInTheDocument()
    expect(api.paymentStatus).toHaveBeenCalledWith("tok-123", "pay-1")
  })
})
