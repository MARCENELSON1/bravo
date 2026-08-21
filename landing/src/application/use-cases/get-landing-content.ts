import type { Faq } from "@/domain/entities/faq"
import type { Feature } from "@/domain/entities/feature"
import type { Integration } from "@/domain/entities/integration"
import type { Step } from "@/domain/entities/step"
import type { ContentRepository } from "@/domain/ports/content-repository"

export interface LandingContent {
  readonly features: readonly Feature[]
  readonly steps: readonly Step[]
  readonly integrations: readonly Integration[]
  readonly faqs: readonly Faq[]
}

// Caso de uso: reunir el contenido editorial de la landing en una sola lectura.
export class GetLandingContent {
  constructor(private readonly content: ContentRepository) {}

  async execute(): Promise<LandingContent> {
    const [features, steps, integrations, faqs] = await Promise.all([
      this.content.getFeatures(),
      this.content.getSteps(),
      this.content.getIntegrations(),
      this.content.getFaqs(),
    ])
    return { features, steps, integrations, faqs }
  }
}
