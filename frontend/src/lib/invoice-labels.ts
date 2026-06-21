import type { DocType, FiscalCondition, InvoiceStatus } from "@/api/types-invoicing"

// ES display labels for the AFIP códigos we expose in the UI.

const INVOICE_TYPE_LABELS: Record<string, string> = {
  FACTURA_A: "Factura A",
  FACTURA_B: "Factura B",
  FACTURA_C: "Factura C",
  NOTA_CREDITO_A: "Nota de crédito A",
  NOTA_CREDITO_B: "Nota de crédito B",
  NOTA_CREDITO_C: "Nota de crédito C",
  NOTA_DEBITO_A: "Nota de débito A",
  NOTA_DEBITO_B: "Nota de débito B",
  NOTA_DEBITO_C: "Nota de débito C",
}

export function invoiceTypeLabel(type: string): string {
  return INVOICE_TYPE_LABELS[type] ?? type
}

export const DOC_TYPE_LABELS: Record<DocType, string> = {
  CONSUMIDOR_FINAL: "Consumidor final",
  CUIT: "CUIT",
  CUIL: "CUIL",
  DNI: "DNI",
}

export const FISCAL_CONDITION_LABELS: Record<FiscalCondition, string> = {
  RESPONSABLE_INSCRIPTO: "Responsable inscripto",
  MONOTRIBUTO: "Monotributo",
}

export const INVOICE_STATUS_LABELS: Record<InvoiceStatus, string> = {
  DRAFT: "Borrador",
  AUTHORIZED: "Autorizada",
  REJECTED: "Rechazada",
}

// Formats a comprobante's point-of-sale + number as AFIP shows it: 0001-00000042.
export function invoiceNumber(pointOfSale: number, number: number | null): string {
  if (number === null) return "—"
  return `${String(pointOfSale).padStart(4, "0")}-${String(number).padStart(8, "0")}`
}
