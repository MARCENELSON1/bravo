// Namespace `invoices` (P3 gestión). Pantalla de comprobantes.
// Los labels de TIPO de comprobante y condición fiscal viven en
// `@/lib/invoice-labels` y quedan EN ESPAÑOL (conceptos fiscales AFIP/ARCA).
export const invoices = {
  title: "Comprobantes",
  subtitle: "Facturas electrónicas emitidas (ARCA). El CAE es la autorización fiscal.",
  columns: {
    invoice: "Comprobante",
    type: "Tipo",
    cae: "CAE",
    status: "Estado",
    total: "Total",
  },
  caeExpiration: "vto. {{date}}",
  statusLabels: {
    DRAFT: "Borrador",
    AUTHORIZED: "Autorizada",
    REJECTED: "Rechazada",
  },
  empty: "Todavía no emitiste comprobantes. Facturá una comanda pagada desde su detalle.",
} as const
