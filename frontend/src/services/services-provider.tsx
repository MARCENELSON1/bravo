import { useMemo } from "react"
import type { ReactNode } from "react"

import { AuthApi } from "@/api/auth-api"
import { FetchHttpClient } from "@/api/http-client"
import { IntegrationsApi } from "@/api/integrations-api"
import { InvoicesApi } from "@/api/invoices-api"
import { OrdersApi } from "@/api/orders-api"
import { PaymentsApi } from "@/api/payments-api"
import { ProductsApi } from "@/api/products-api"
import { ReportsApi } from "@/api/reports-api"
import { TablesApi } from "@/api/tables-api"
import { API_BASE_URL } from "@/lib/env"
import { ServicesContext } from "@/services/services-context"
import type { Services } from "@/services/services-context"

export function ServicesProvider({
  children,
  value,
}: {
  children: ReactNode
  value?: Services
}) {
  const services = useMemo<Services>(() => {
    if (value) return value
    const http = new FetchHttpClient(API_BASE_URL)
    return {
      authApi: new AuthApi(http),
      integrationsApi: new IntegrationsApi(http),
      invoicesApi: new InvoicesApi(http),
      ordersApi: new OrdersApi(http),
      paymentsApi: new PaymentsApi(http),
      productsApi: new ProductsApi(http),
      reportsApi: new ReportsApi(http),
      tablesApi: new TablesApi(http),
    }
  }, [value])
  return <ServicesContext.Provider value={services}>{children}</ServicesContext.Provider>
}
