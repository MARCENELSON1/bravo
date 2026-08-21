import { GetLandingContent } from "@/application/use-cases/get-landing-content"
import { GetPricingPlans } from "@/application/use-cases/get-pricing-plans"
import { SubmitLead } from "@/application/use-cases/submit-lead"
import { loadConfig, type AppConfig } from "@/infrastructure/config/app-config"
import { HttpLeadGateway } from "@/infrastructure/gateways/http-lead-gateway"
import { StaticContentRepository } from "@/infrastructure/repositories/static-content-repository"
import { StaticPlanRepository } from "@/infrastructure/repositories/static-plan-repository"

// Composition root: el ÚNICO lugar que conoce las implementaciones concretas.
// Acá se elige qué adapter cumple cada puerto y se inyectan por constructor en los
// casos de uso. Cambiar de datos estáticos a HTTP es cambiar solo estas líneas.
export interface Container {
  readonly config: AppConfig
  readonly getPricingPlans: GetPricingPlans
  readonly getLandingContent: GetLandingContent
  readonly submitLead: SubmitLead
}

export function createContainer(): Container {
  const config = loadConfig()

  // Adapters (infrastructure) → cumplen los puertos del dominio.
  const planRepository = new StaticPlanRepository()
  const contentRepository = new StaticContentRepository()
  const leadGateway = new HttpLeadGateway(config.apiUrl)

  // Casos de uso (application) ← reciben los puertos, no las clases concretas.
  return {
    config,
    getPricingPlans: new GetPricingPlans(planRepository),
    getLandingContent: new GetLandingContent(contentRepository),
    submitLead: new SubmitLead(leadGateway),
  }
}
