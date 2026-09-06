import type { Feature } from "@/domain/entities/feature"
import type { Step } from "@/domain/entities/step"
import type { ContentRepository } from "@/domain/ports/content-repository"

export interface LandingContent {
  readonly features: readonly Feature[]
  readonly steps: readonly Step[]
}

// Caso de uso: reunir el contenido editorial de la landing en una sola lectura.
export class GetLandingContent {
  constructor(private readonly content: ContentRepository) {}

  execute(): LandingContent {
    return { features: this.content.getFeatures(), steps: this.content.getSteps() }
  }
}
