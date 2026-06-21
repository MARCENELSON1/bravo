import { createContext, useContext } from "react"

import type { AuthApi } from "@/api/auth-api"
import type { IntegrationsApi } from "@/api/integrations-api"
import type { InvoicesApi } from "@/api/invoices-api"
import type { OrdersApi } from "@/api/orders-api"
import type { PaymentsApi } from "@/api/payments-api"
import type { ProductsApi } from "@/api/products-api"
import type { ReportsApi } from "@/api/reports-api"
import type { TablesApi } from "@/api/tables-api"
import type { TimeClockApi } from "@/api/timeclock-api"

// DI for the data layer. The context + hook live here (no component) so the
// provider file can export only a component (Fast Refresh friendly). Tests pass
// fakes via the provider's `value` — the equivalent of overriding a DI provider.
export interface Services {
  authApi: AuthApi
  integrationsApi: IntegrationsApi
  invoicesApi: InvoicesApi
  ordersApi: OrdersApi
  paymentsApi: PaymentsApi
  productsApi: ProductsApi
  reportsApi: ReportsApi
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
