// Namespace `expenses`: egresos (expenses-page).
export const expenses = {
  title: "Egresos",
  subtitle: "Registrá y seguí las salidas de plata.",
  new: "Nuevo egreso",
  // Medios de pago (código = enum, no cambia).
  methodLabels: {
    CASH: "Efectivo",
    TRANSFER: "Transferencia",
    CARD: "Tarjeta",
    MERCADOPAGO: "MercadoPago",
  },
  form: {
    description: "Una salida de plata (proveedor, gasto, etc.).",
    amountPlaceholder: "Monto",
    categoryPlaceholder: "Rubro (p. ej. Proveedores)",
    counterpartyPlaceholder: "Contraparte (p. ej. Frigorífico Sur)",
    descriptionPlaceholder: "Descripción (opcional)",
    submit: "Registrar egreso",
    submitting: "Registrando…",
    invalidAmount: "Ingresá un monto válido.",
    success: "Egreso registrado.",
    error: "No pudimos registrar el egreso.",
  },
  table: {
    counterparty: "Contraparte",
    category: "Rubro",
    method: "Medio",
    amount: "Monto",
  },
  empty: "Todavía no registraste egresos.",
} as const
