import { useMemo } from "react"
import type { ReactNode } from "react"

import { AdvisorApi } from "@/api/advisor-api"
import { AnalyticsApi } from "@/api/analytics-api"
import { AuthApi } from "@/api/auth-api"
import { BillingApi } from "@/api/billing-api"
import { CashApi } from "@/api/cash-api"
import { CopilotApi } from "@/api/copilot-api"
import { CustomersApi } from "@/api/customers-api"
import { FinanceApi } from "@/api/finance-api"
import { FloorApi } from "@/api/floor-api"
import { FetchHttpClient } from "@/api/http-client"
import { IntegrationsApi } from "@/api/integrations-api"
import { InventoryApi } from "@/api/inventory-api"
import { InvoicesApi } from "@/api/invoices-api"
import { OrdersApi } from "@/api/orders-api"
import { PaymentsApi } from "@/api/payments-api"
import { PlatformApi } from "@/api/platform-api"
import { ProductsApi } from "@/api/products-api"
import { PublicMenuApi } from "@/api/public-menu-api"
import { RealtimeApi } from "@/api/realtime-api"
import { ReportsApi } from "@/api/reports-api"
import { ReservationsApi } from "@/api/reservations-api"
import { SectorsApi } from "@/api/sectors-api"
import { TablesApi } from "@/api/tables-api"
import { TenantsApi } from "@/api/tenants-api"
import { TimeClockApi } from "@/api/timeclock-api"
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
      advisorApi: new AdvisorApi(http),
      analyticsApi: new AnalyticsApi(http),
      financeApi: new FinanceApi(http),
      authApi: new AuthApi(http),
      billingApi: new BillingApi(http),
      cashApi: new CashApi(http),
      copilotApi: new CopilotApi(http),
      customersApi: new CustomersApi(http),
      floorApi: new FloorApi(http),
      integrationsApi: new IntegrationsApi(http),
      inventoryApi: new InventoryApi(http),
      invoicesApi: new InvoicesApi(http),
      ordersApi: new OrdersApi(http),
      paymentsApi: new PaymentsApi(http),
      platformApi: new PlatformApi(http),
      productsApi: new ProductsApi(http),
      publicMenuApi: new PublicMenuApi(http),
      realtimeApi: new RealtimeApi(http),
      reportsApi: new ReportsApi(http),
      reservationsApi: new ReservationsApi(http),
      sectorsApi: new SectorsApi(http),
      tablesApi: new TablesApi(http),
      tenantsApi: new TenantsApi(http),
      timeClockApi: new TimeClockApi(http),
    }
  }, [value])
  return <ServicesContext.Provider value={services}>{children}</ServicesContext.Provider>
}
