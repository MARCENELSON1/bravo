import { describe, expect, it, vi } from "vitest"
import { screen } from "@testing-library/react"

import type { TablesApi } from "@/api/tables-api"
import type { TableDTO } from "@/api/types-operations"
import { TableQrPage } from "@/features/floor/table-qr-page"
import type { Services } from "@/services/services-context"
import { renderWithProviders } from "@/test/test-utils"

const TABLES: TableDTO[] = [
  { id: "t1", number: 7, name: null, active: true, sector_id: null, capacity: null },
  { id: "t2", number: 8, name: null, active: false, sector_id: null, capacity: null },
]

function renderPage() {
  const tablesApi = {
    list: vi.fn().mockResolvedValue(TABLES),
    qr: vi
      .fn()
      .mockResolvedValue({ token: "tok-t1", url: "https://app.wellnod.com/carta/tok-t1" }),
  } as unknown as TablesApi
  renderWithProviders(<TableQrPage />, { services: { tablesApi } as Partial<Services> })
  return tablesApi
}

describe("TableQrPage", () => {
  it("lists active tables with a printable QR and skips inactive ones", async () => {
    renderPage()

    expect(await screen.findByText("Mesa 7")).toBeInTheDocument()
    // The QR loaded (its caption only shows when the token resolved).
    expect(await screen.findByText("Escaneá para ver la carta")).toBeInTheDocument()
    // Inactive table 8 is not printed.
    expect(screen.queryByText("Mesa 8")).not.toBeInTheDocument()
    expect(screen.getByRole("button", { name: /imprimir/i })).toBeInTheDocument()
  })
})
