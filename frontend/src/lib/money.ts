// Format a money amount (integer minor units + ISO-4217 currency) for display.
export function formatMoney(amount: number, currency: string): string {
  return new Intl.NumberFormat("es-AR", {
    style: "currency",
    currency,
  }).format(amount / 100)
}
