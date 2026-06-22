// DTOs for the advisor API. Amounts are integer minor units; ratios in bps.

export interface AdvisorKpisDTO {
  currency: string
  period_days: number
  sales_amount: number
  food_cost_amount: number
  labor_cost_amount: number
  other_fixed_amount: number
  waste_amount: number
  gross_margin_amount: number
  net_margin_amount: number
  food_cost_ratio_bps: number
  labor_cost_ratio_bps: number
  prime_cost_ratio_bps: number
  break_even_amount: number
  orders_count: number
  average_ticket_amount: number
  no_show_rate_bps: number
  configured: boolean
}

export interface NarratedInsightDTO {
  code: string
  severity: string
  bucket: string
  title: string
  body: string
  action: string
}

export interface AdvisorReportDTO {
  kpis: AdvisorKpisDTO
  insights: NarratedInsightDTO[]
  summary: string | null
  llm_enabled: boolean
}

export interface AdvisorSettingsDTO {
  monthly_labor_cost: number
  monthly_other_fixed_costs: number
  target_food_cost_bps: number
  currency: string
  configured: boolean
}

export interface UpdateAdvisorSettingsBody {
  monthly_labor_cost: number
  monthly_other_fixed_costs: number
  target_food_cost_bps: number
}

export interface AdvisorQuery {
  from?: string
  to?: string
}
