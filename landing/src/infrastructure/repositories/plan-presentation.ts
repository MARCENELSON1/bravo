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

// Solo INTL (inglés): es la única región que lee los planes por HTTP. AR sigue en
// StaticPlanRepository (fuente única, sin duplicar el copy acá). Las claves son el
// PlanTier del backend (BASIC/PRO/ENTERPRISE).
const INTL: Readonly<Record<string, PlanPresentation>> = {
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
}

export function presentationFor(region: Region, tier: string): PlanPresentation | null {
  if (region !== "INTL") return null
  return INTL[tier] ?? null
}
