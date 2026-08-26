import type { Currency } from "@/domain/value-objects/money"

// Value Object: la región de la landing. Decide idioma, moneda y qué pasarela de
// cobro aplica (el candado anti-arbitraje vive en el backend; acá solo el display).
// AR = Argentina (español, ARS, MercadoPago) · INTL = resto del mundo (inglés, USD,
// Stripe). Binaria a propósito: el precio barato es específico del mercado local.
export type Region = "AR" | "INTL"
export type Locale = "es-AR" | "en-US"

export const LOCALE_BY_REGION: Record<Region, Locale> = {
  AR: "es-AR",
  INTL: "en-US",
}

export const CURRENCY_BY_REGION: Record<Region, Currency> = {
  AR: "ARS",
  INTL: "USD",
}

/** Deriva la región del atributo lang del HTML servido (para hidratar sin mismatch). */
export function regionFromLang(lang: string | null | undefined): Region {
  return (lang ?? "").toLowerCase().startsWith("en") ? "INTL" : "AR"
}
