import type { Feature } from "@/domain/entities/feature"
import type { Step } from "@/domain/entities/step"

// Puerto (driven port): contenido editorial de la landing (features y pasos).
// Separado de PlanRepository (ISP): quien solo necesita
// contenido no arrastra la lógica de planes.
// Síncrono a propósito: es contenido estático y tiene que estar en el HTML que
// se prerenderiza (ver scripts/prerender.mjs). Una Promise acá obligaba a llenarlo
// en un efecto, y los efectos no corren en el render del servidor.
export interface ContentRepository {
  getFeatures(): readonly Feature[]
  getSteps(): readonly Step[]
}
