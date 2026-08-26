import { GetLandingContent } from "@/application/use-cases/get-landing-content"
import { GetPricingPlans } from "@/application/use-cases/get-pricing-plans"
import { SubmitLead } from "@/application/use-cases/submit-lead"
import { LOCALE_BY_REGION, type Locale, type Region } from "@/domain/value-objects/region"
import { loadConfig, type AppConfig } from "@/infrastructure/config/app-config"
import { HttpLeadGateway } from "@/infrastructure/gateways/http-lead-gateway"
import { EnStaticContentRepository } from "@/infrastructure/repositories/en-static-content-repository"
import { HttpPlanRepository } from "@/infrastructure/repositories/http-plan-repository"
import { StaticContentRepository } from "@/infrastructure/repositories/static-content-repository"

// Composition root: el ÚNICO lugar que conoce las implementaciones concretas.
// Acá se elige qué adapter cumple cada puerto por región y se inyectan por
// constructor en los casos de uso. El seam anti-arbitraje del DISPLAY vive acá.
export interface Container {
  readonly config: AppConfig
  readonly region: Region
  readonly locale: Locale
  readonly getPricingPlans: GetPricingPlans
  readonly getLandingContent: GetLandingContent
  readonly submitLead: SubmitLead
}

// region default "AR" preserva el comportamiento actual (Argentina) sin romper nada.
// INTL (inglés/USD) usa contenido transcreado + planes por HTTP desde el backend.
export function createContainer(region: Region = "AR"): Container {
  const config = loadConfig()

  // Adapters (infrastructure) elegidos por región → cumplen los puertos del dominio.
  // El PRECIO sale del catálogo del backend (/public/plans, editable desde el panel,
  // no hardcodeado) para AR y para INTL. El CONTENIDO cambia por idioma.
  const planRepository = new HttpPlanRepository(config.apiUrl, region)
  const contentRepository =
    region === "INTL" ? new EnStaticContentRepository() : new StaticContentRepository()
  const leadGateway = new HttpLeadGateway(config.apiUrl)

  // Casos de uso (application) ← reciben los puertos, no las clases concretas.
  return {
    config,
    region,
    locale: LOCALE_BY_REGION[region],
    getPricingPlans: new GetPricingPlans(planRepository),
    getLandingContent: new GetLandingContent(contentRepository),
    submitLead: new SubmitLead(leadGateway),
  }
}
