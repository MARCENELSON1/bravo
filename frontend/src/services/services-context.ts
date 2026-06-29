import { createContext, useContext } from "react"

import type { AdvisorApi } from "@/api/advisor-api"
import type { AnalyticsApi } from "@/api/analytics-api"
import type { AuthApi } from "@/api/auth-api"
import type { CashApi } from "@/api/cash-api"
import type { CopilotApi } from "@/api/copilot-api"
import type { FinanceApi } from "@/api/finance-api"
import type { FloorApi } from "@/api/floor-api"
import type { IntegrationsApi } from "@/api/integrations-api"
import type { InventoryApi } from "@/api/inventory-api"
import type { InvoicesApi } from "@/api/invoices-api"
import type { OrdersApi } from "@/api/orders-api"
import type { PaymentsApi } from "@/api/payments-api"
import type { ProductsApi } from "@/api/products-api"
import type { RealtimeApi } from "@/api/realtime-api"
import type { ReportsApi } from "@/api/reports-api"
import type { ReservationsApi } from "@/api/reservations-api"
import type { TablesApi } from "@/api/tables-api"
import type { TimeClockApi } from "@/api/timeclock-api"

// DI for the data layer. The context + hook live here (no component) so the
// provider file can export only a component (Fast Refresh friendly). Tests pass
// fakes via the provider's `value` — the equivalent of overriding a DI provider.
export interface Services {
  advisorApi: AdvisorApi
  analyticsApi: AnalyticsApi
  authApi: AuthApi
  cashApi: CashApi
  copilotApi: CopilotApi
  financeApi: FinanceApi
  floorApi: FloorApi
  integrationsApi: IntegrationsApi
  inventoryApi: InventoryApi
  invoicesApi: InvoicesApi
  ordersApi: OrdersApi
  paymentsApi: PaymentsApi
  productsApi: ProductsApi
  realtimeApi: RealtimeApi
  reportsApi: ReportsApi
  reservationsApi: ReservationsApi
  tablesApi: TablesApi
  timeClockApi: TimeClockApi
}

export const ServicesContext = createContext<Services | null>(null)

export function useServices(): Services {
  const ctx = useContext(ServicesContext)
  if (!ctx) {
    throw new Error("useServices must be used within a ServicesProvider")
  }
  return ctx
}
