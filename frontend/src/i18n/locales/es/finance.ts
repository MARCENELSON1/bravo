// Namespace `finance` (P3 gestión). Pantalla de Finanzas + tarjetas de gestión.
export const finance = {
  title: "Finanzas",
  loadError: "No pudimos cargar las finanzas.",
  loading: "Cargando…",
  ranges: {
    today: "Hoy",
    week: "Esta semana",
    month: "Este mes",
    quarter: "Trimestre",
  },
  kpiLabels: {
    prime_cost: "Prime Cost",
    food_cost: "Food Cost",
    labor_cost: "Costo de personal",
    waste: "Mermas",
    net_margin: "Margen neto",
    gross_margin: "Margen bruto",
    break_even: "Punto de equilibrio",
    revpash: "RevPASH",
    inventory_turnover: "Rotación de inventario",
  },
  statusActions: {
    healthy: "Mantener",
    warn: "Revisar",
    alert: "Actuar",
    neutral: "—",
  },
  healthyRange: "sano {{low}}–{{high}}",
  healthyMax: "sano < {{high}}",
  configureCosts:
    "Cargá tus costos fijos (personal y otros) en el Asesor para que el margen neto y el prime cost sean exactos.",
  hero: {
    netProfit: "Tu ganancia neta del período",
    vsPrevious: "vs período anterior",
    projectionPrefix: "Si seguís así, cerrás en",
    projectionDays: "({{elapsed}}/{{total}} días)",
  },
  commissions: {
    label: "Comisiones de cobro (pasarelas)",
    netCollected: "Cobrado neto de comisiones:",
  },
  diagnostics: {
    title: "Diagnósticos",
  },
  productMargins: {
    title: "Margen de contribución por producto",
    product: "Producto",
    unitsMargin: "Unidades · Margen",
    noLines: "Sin líneas en el período.",
  },
  exports: {
    title: "Exportar para el contador",
    description:
      "Descargá los datos del período en CSV (apto Excel). Se abre con acentos y separado por punto y coma.",
    error: "No pudimos generar el archivo.",
    items: {
      sales: { label: "Ventas (CSV)", filename: "ventas-por-dia.csv" },
      expenses: { label: "Gastos (CSV)", filename: "gastos.csv" },
      vat_sales: { label: "Libro IVA Ventas (CSV)", filename: "libro-iva-ventas.csv" },
    },
  },
  commissionRates: {
    title: "Comisiones por medio de pago",
    descPre:
      "Lo que se queda la pasarela de cada cobro. Con esto, el Inicio te muestra la ganancia",
    descEm: "real",
    descPost: "después de comisiones. Vacío = 0%.",
    invalid: "Comisión inválida (entre 0 y 100%).",
    saved: "Comisiones guardadas.",
    saveError: "No pudimos guardar las comisiones.",
    save: "Guardar comisiones",
    saving: "Guardando…",
  },
  paymentMethods: {
    CARD: "Tarjeta",
    MERCADOPAGO: "MercadoPago",
    QR: "QR",
  },
  expenseChanges: {
    title: "Los 3 gastos que más cambiaron",
    empty: "Sin cambios relevantes vs el período anterior.",
    legend: "▲ subió vs el período anterior · ▼ bajó",
  },
  expenseDonut: {
    title: "Distribución de gastos",
    empty: "Sin gastos registrados en el período.",
    other: "Otros",
  },
  recentMovements: {
    title: "Últimos movimientos",
    loading: "Cargando…",
    empty: "Sin movimientos en el período.",
    income: "Cobro",
    expense: "Egreso",
  },
} as const
