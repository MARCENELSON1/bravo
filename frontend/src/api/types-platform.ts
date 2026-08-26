// Panel de plataforma (super-admin): catálogo global de planes del SaaS.

export interface PlatformAccessDTO {
  platform_admin: boolean
}

export interface FeatureDTO {
  key: string
  label: string
}

export interface PlatformPlanDTO {
  id: string
  tier: string
  region: string
  amount: number // minor units (centavos)
  currency: string
  interval: string
  features: string[]
  active: boolean
}

export interface PlatformPlanInput {
  id?: string | null // null/omitido → crear; presente → actualizar
  tier: string
  region: string
  amount: number // minor units
  currency: string
  interval?: string
  features: string[]
  active: boolean
}
