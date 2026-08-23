// ISO-4217 currency → the locale whose number conventions we format with.
// ARS stays on es-AR (today's exact rendering → paridad); USD gets US
// conventions ($1,234.56). Unknown currencies fall back to es-AR.
const LOCALE_BY_CURRENCY: Record<string, string> = {
  ARS: "es-AR",
  USD: "en-US",
}

function localeFor(currency: string): string {
  return LOCALE_BY_CURRENCY[(currency ?? "").toUpperCase()] ?? "es-AR"
}

// Format a money amount (integer minor units + ISO-4217 currency) for display.
// The number/symbol conventions follow the currency's locale (ARS → es-AR,
// USD → en-US), so a US tenant sees "$1,234.56" and an AR tenant is unchanged.
// `fractionDigits` opcional: pasar 0 para ocultar los centavos (por defecto, 2).
export function formatMoney(amount: number, currency: string, fractionDigits?: number): string {
  return new Intl.NumberFormat(localeFor(currency), {
    style: "currency",
    currency,
    ...(fractionDigits != null
      ? { minimumFractionDigits: fractionDigits, maximumFractionDigits: fractionDigits }
      : {}),
  }).format(amount / 100)
}
