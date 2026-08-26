// Namespace `invoices` (P3 management). Invoices screen.
// Los labels de TIPO de comprobante y condición fiscal viven en
// `@/lib/invoice-labels` y quedan EN ESPAÑOL (conceptos fiscales AFIP/ARCA).
export const invoices = {
  title: "Invoices",
  subtitle: "Electronic invoices issued (ARCA). The CAE is the tax authorization.",
  columns: {
    invoice: "Invoice",
    type: "Type",
    cae: "CAE",
    status: "Status",
    total: "Total",
  },
  caeExpiration: "exp. {{date}}",
  statusLabels: {
    DRAFT: "Draft",
    AUTHORIZED: "Authorized",
    REJECTED: "Rejected",
  },
  empty: "You haven't issued any invoices yet. Bill a paid order from its detail.",
} as const
