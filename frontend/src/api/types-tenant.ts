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
