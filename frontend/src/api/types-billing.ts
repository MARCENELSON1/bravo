// Suscripción del SaaS (Flujo A), lado tenant. La región (AR/INTL) sale del país
// del local; determina moneda y riel (Stripe/MercadoPago) — el candado anti-arbitraje.

export interface BillingPlanDTO {
  id: string
  tier: string
  region: string
  amount: number // minor units (centavos)
  currency: string
  interval: string
  features: string[]
}

export interface SubscriptionDTO {
  status: string
  plan_id: string
  region: string
  rail: string
  grants_access: boolean
  current_period_end: string | null
}

export interface CheckoutResponseDTO {
  url: string // a dónde redirigir para pagar (checkout hosteado)
}
