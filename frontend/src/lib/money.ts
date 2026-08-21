// Format a money amount (integer minor units + ISO-4217 currency) for display.
// `fractionDigits` opcional: pasar 0 para ocultar los centavos (por defecto, 2).
export function formatMoney(amount: number, currency: string, fractionDigits?: number): string {
  return new Intl.NumberFormat("es-AR", {
    style: "currency",
    currency,
    ...(fractionDigits != null
      ? { minimumFractionDigits: fractionDigits, maximumFractionDigits: fractionDigits }
      : {}),
  }).format(amount / 100)
}
