// DTOs for the analytics API (gold KPIs over the canonical model).
// Amounts are integer minor units (centavos) in the tenant's currency.

export interface RevenueSummaryDTO {
  currency: string
  sales_amount: number
  collected_amount: number
  expense_amount: number
  food_cost_amount: number
  gross_margin_amount: number
  orders_count: number
  average_ticket_amount: number
}

export interface PaymentMixRowDTO {
  method: string
  direction: string
  amount: number
  count: number
}

export interface ProductPerformanceRowDTO {
  product_id: string
  product_name: string
  units_sold: number
  sales_amount: number
  food_cost_amount: number
  margin_amount: number
  currency: string
}

export interface AnalyticsQuery {
  from?: string
  to?: string
  limit?: number
}
