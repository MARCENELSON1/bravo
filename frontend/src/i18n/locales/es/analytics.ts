// Namespace `analytics` (P3 gestión): pantalla de analítica (KPIs, mix de medios
// de pago, productos más vendidos).
export const analytics = {
  title: "Analítica",
  description:
    "Tus números en pesos, leídos del modelo canónico. Dejá las fechas vacías para ver todo.",
  dateFrom: "Desde",
  dateTo: "Hasta",
  kpis: {
    sales: "Ventas",
    collected: "Cobrado",
    expenses: "Egresos",
    grossMargin: "Margen bruto",
    grossMarginHint: "Ventas − food cost",
    averageTicket: "Ticket promedio",
    foodCost: "Food cost",
  },
  // Cantidad de comandas (glosario: Comanda = Order).
  ordersCount_one: "{{count}} comanda",
  ordersCount_other: "{{count}} comandas",
  paymentMix: {
    title: "Mix de medios de pago",
    hint: "Montos en bruto (antes de comisiones de pasarela). Lo cobrado neto de comisiones lo ves en Finanzas y en el Inicio.",
    method: "Medio",
    type: "Tipo",
    operations: "Operaciones",
    amount: "Monto",
    empty: "Sin pagos en el período.",
  },
  topProducts: {
    title: "Productos más vendidos",
    product: "Producto",
    units: "Unidades",
    sales: "Ventas",
    foodCost: "Food cost",
    margin: "Margen",
    empty: "Sin ventas en el período.",
  },
  // Medios de pago (código = enum, no cambia).
  methodLabels: {
    CASH: "Efectivo",
    CARD: "Tarjeta",
    TRANSFER: "Transferencia",
    MERCADOPAGO: "MercadoPago",
    QR: "QR",
  },
  // Dirección del movimiento (código = enum, no cambia).
  directionLabels: {
    INFLOW: "Ingreso",
    OUTFLOW: "Egreso",
  },
} as const
