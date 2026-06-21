// DTOs for Fase 4 (facturación electrónica AFIP), mirroring the backend contract.

export type InvoiceStatus = "DRAFT" | "AUTHORIZED" | "REJECTED"

export type DocType = "CUIT" | "CUIL" | "DNI" | "CONSUMIDOR_FINAL"

export type FiscalCondition = "RESPONSABLE_INSCRIPTO" | "MONOTRIBUTO"

export interface InvoiceDTO {
  id: string
  type: string // FACTURA_A | FACTURA_B | FACTURA_C | NOTA_*  (display-mapped)
  point_of_sale: number
  number: number | null
  doc_type: string
  doc_number: string
  net: number // minor units (centavos)
  vat: number
  total: number
  currency: string
  status: InvoiceStatus
  cae: string | null
  cae_expiration: string | null // ISO date
  order_id: string | null
  rejection: string | null
}

export interface IssueInvoiceBody {
  doc_type: DocType
  doc_number: string
}

// --- AFIP connection (per-tenant credentials) ---

export interface AfipConnectionDTO {
  connected: boolean
  cuit: string | null
  point_of_sale: number | null
  fiscal_condition: string | null
  live_mode: boolean
}

export interface AfipConnectBody {
  cuit: string
  certificate: string
  private_key: string
  point_of_sale: number
  fiscal_condition: FiscalCondition
}
