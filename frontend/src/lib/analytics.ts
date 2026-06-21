export const PAYMENT_METHOD_LABELS: Record<string, string> = {
  CASH: "Efectivo",
  CARD: "Tarjeta",
  TRANSFER: "Transferencia",
  MERCADOPAGO: "MercadoPago",
  QR: "QR",
}

export const PAYMENT_DIRECTION_LABELS: Record<string, string> = {
  INFLOW: "Ingreso",
  OUTFLOW: "Egreso",
}

export function methodLabel(method: string): string {
  return PAYMENT_METHOD_LABELS[method] ?? method
}

export function directionLabel(direction: string): string {
  return PAYMENT_DIRECTION_LABELS[direction] ?? direction
}
