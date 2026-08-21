// Value Object: importe + moneda. Inmutable y sin dependencias de framework.
export type Currency = "ARS" | "USD"

export interface Money {
  readonly amount: number
  readonly currency: Currency
}

export function money(amount: number, currency: Currency = "ARS"): Money {
  return { amount, currency }
}

/** Aplica un descuento porcentual (0–1) devolviendo un nuevo Money. */
export function withDiscount(value: Money, ratio: number): Money {
  const factor = Math.min(Math.max(1 - ratio, 0), 1)
  return { ...value, amount: Math.round(value.amount * factor) }
}

/** Formatea para mostrar (es-AR por defecto). $0 se muestra como "Gratis". */
export function formatMoney(value: Money, locale = "es-AR"): string {
  if (value.amount === 0) return "Gratis"
  return new Intl.NumberFormat(locale, {
    style: "currency",
    currency: value.currency,
    maximumFractionDigits: 0,
  }).format(value.amount)
}
