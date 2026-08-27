import type { PlanFeature } from "@/domain/entities/plan"
import type { Region } from "@/domain/value-objects/region"

// Presentación de marketing de un plan (nombre, tagline, bullets). Es copy de
// vidriera, NO dato de negocio: el precio/ciclo/features-habilitadas salen del
// backend (/public/plans, editable desde el panel). Se mergean por tier.
export interface PlanPresentation {
  readonly name: string
  readonly tagline: string
  readonly featured: boolean
  readonly badge?: string
  readonly ctaLabel: string
  readonly features: readonly PlanFeature[]
}

// Las claves son el PlanTier del backend (BASIC/PRO/ENTERPRISE). Las dos regiones
// leen el PRECIO del panel; acá solo vive el copy por idioma.
const PRESENTATION: Readonly<Record<Region, Readonly<Record<string, PlanPresentation>>>> = {
  AR: {
    BASIC: {
      name: "Emprendé",
      tagline: "Para arrancar y digitalizar tu local.",
      featured: false,
      ctaLabel: "Empezá la prueba",
      features: [
        { label: "1 local", included: true },
        { label: "Comandas digitales (mozo → cocina)", included: true },
        { label: "Cobros y facturación ARCA", included: true },
        { label: "Hasta 3 usuarios", included: true },
        { label: "Copiloto IA", included: false },
        { label: "Reportes avanzados", included: false },
      ],
    },
    PRO: {
      name: "Profesional",
      tagline: "El local que quiere crecer con datos.",
      featured: true,
      badge: "Más elegido",
      ctaLabel: "Empezá la prueba",
      features: [
        { label: "1 local", included: true },
        { label: "Todo lo de Emprendé", included: true },
        { label: "Copiloto IA en español", included: true },
        { label: "KDS de cocina y barra", included: true },
        { label: "Fichaje de empleados", included: true },
        { label: "Reportes en tiempo real", included: true },
        { label: "Usuarios ilimitados", included: true },
      ],
    },
    ENTERPRISE: {
      name: "Multi-local",
      tagline: "Para cadenas y varios puntos de venta.",
      featured: false,
      ctaLabel: "Hablá con ventas",
      features: [
        { label: "Locales ilimitados", included: true },
        { label: "Todo lo de Profesional", included: true },
        { label: "Panel consolidado multi-local", included: true },
        { label: "Roles y permisos avanzados", included: true },
        { label: "Integraciones y API", included: true },
        { label: "Soporte prioritario", included: true },
      ],
    },
  },
  INTL: {
    BASIC: {
      name: "Starter",
      tagline: "To get started and go digital.",
      featured: false,
      ctaLabel: "Start 30-day trial",
      features: [
        { label: "1 location", included: true },
        { label: "Digital order taking (server → kitchen)", included: true },
        { label: "Payments & sales tax", included: true },
        { label: "Up to 3 users", included: true },
        { label: "AI copilot", included: false },
        { label: "Advanced reporting", included: false },
      ],
    },
    PRO: {
      name: "Professional",
      tagline: "For the restaurant that wants to grow with data.",
      featured: true,
      badge: "Most popular",
      ctaLabel: "Start 30-day trial",
      features: [
        { label: "1 location", included: true },
        { label: "Everything in Starter", included: true },
        { label: "AI copilot in English", included: true },
        { label: "Kitchen & bar KDS", included: true },
        { label: "Employee time tracking", included: true },
        { label: "Real-time reporting", included: true },
        { label: "Unlimited users", included: true },
      ],
    },
    ENTERPRISE: {
      name: "Multi-location",
      tagline: "For chains and multiple locations.",
      featured: false,
      ctaLabel: "Talk to sales",
      features: [
        { label: "Unlimited locations", included: true },
        { label: "Everything in Professional", included: true },
        { label: "Consolidated multi-location dashboard", included: true },
        { label: "Advanced roles & permissions", included: true },
        { label: "Integrations & API", included: true },
        { label: "Priority support", included: true },
      ],
    },
  },
}

export function presentationFor(region: Region, tier: string): PlanPresentation | null {
  return PRESENTATION[region][tier] ?? null
}
