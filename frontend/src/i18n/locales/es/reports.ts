// Namespace `reports` (P3 gestión): pantalla de Reportes — resumen del período,
// ventas por día, gastos por rubro, sales tax a remitir, reporte al fisco y top
// productos.
export const reports = {
  title: "Reportes",
  // Selector de rango (el enum vive en lib/finance-range; sólo el label acá).
  ranges: {
    today: "Hoy",
    week: "Esta semana",
    month: "Este mes",
    quarter: "Trimestre",
  },
  summary: {
    title: "Resumen del período",
    sales: "Ventas",
    collectedNet: "Cobrado neto",
    expenses: "Gastos",
    profit: "Ganancia",
    avgTicket: "Ticket prom.",
    orders: "Órdenes",
    error: "No pudimos cargar el resumen.",
  },
  salesByDay: {
    title: "Ventas por día",
    empty: "Sin ventas en el período.",
  },
  expensesByCategory: {
    title: "Gastos por rubro",
    empty: "Sin gastos en el período.",
    total: "Total",
  },
  taxToRemit: {
    title: "Sales tax cobrado",
    description:
      "Lo que cobraste de impuesto en el período — a remitir al fisco (no es ganancia).",
  },
  taxReport: {
    title: "Reporte al fisco (TaxJar)",
    pending_one: "{{count}} venta por reportar",
    pending_other: "{{count}} ventas por reportar",
    errorsSuffix: " — {{count}} con error",
    allReported_one: "Todo reportado. {{count}} venta presentada.",
    allReported_other: "Todo reportado. {{count}} ventas presentadas.",
    failedNote:
      "Las fallidas se reintentan. Si persisten, revisá que TaxJar esté conectado en Config.",
    reportNow: "Reportar ahora",
    reporting: "Reportando…",
    upToDate: "Al día",
    reportPartialError: "Reportadas {{sent}}. {{failed}} con error — reintentá o revisá TaxJar.",
    reportSuccess: "Reportadas {{sent}} ventas a TaxJar.",
    reportNothing: "No había ventas por reportar.",
    reportError: "No pudimos reportar ahora. Probá de nuevo.",
  },
  topProducts: {
    title: "Top productos",
    empty: "Sin ventas de productos en el período.",
    product: "Producto",
    units: "Unidades",
    sales: "Ventas",
    margin: "Margen",
  },
} as const
