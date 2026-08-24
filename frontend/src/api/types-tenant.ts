// Datos fiscales/regionales del local (Fase 2 internacionalización).
export interface FiscalSettingsDTO {
  country: string
  currency: string
  tax_regime: string
  tax_engine: string
  street: string | null
  city: string | null
  state: string | null
  zip: string | null
}

export interface FiscalAddressInput {
  street: string | null
  city: string | null
  state: string | null
  zip: string | null
}

// Impuesto a sumar sobre una orden (minor units). AR/IVA → tax 0 (incluido);
// US → lo devuelve el motor (TaxJar) según la dirección fiscal del local.
export interface TaxQuoteDTO {
  subtotal_amount: number
  tax_amount: number
  total_amount: number
  currency: string
  rate_bps: number
  jurisdiction: string | null
}
