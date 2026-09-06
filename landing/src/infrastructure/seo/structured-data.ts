/**
 * JSON-LD para motores de búsqueda y de respuesta.
 *
 * Se genera en tiempo de build desde los MISMOS repositorios que alimentan la
 * pantalla. Escrito a mano se desincronizaría: cambiás un precio en el
 * repositorio y el structured data seguiría diciendo el viejo. Así no puede pasar.
 * Por región (AR/INTL): país, idioma y URL cambian según la variante servida.
 */
import type { Container } from "@/infrastructure/di/container"
import { formatMoney } from "@/domain/value-objects/money"
import { seoMetaFor } from "@/infrastructure/seo/meta"

const SITE = "https://wellnod.com"

const REGION_SD = {
  AR: {
    country: "Argentina",
    inLanguage: "es-AR",
    description:
      "Sistema de gestión para restaurantes, bares y cafés: comandas digitales, " +
      "cobros, facturación electrónica y copiloto de IA.",
  },
  INTL: {
    country: "United States",
    inLanguage: "en-US",
    description:
      "Restaurant management system for restaurants, bars and cafés: digital order " +
      "taking, card payments, automated sales tax, and an AI copilot.",
  },
} as const

export async function buildStructuredData(container: Container): Promise<string> {
  // Los planes de INTL salen por HTTP; si el backend no está disponible en build,
  // el JSON-LD sale sin offers (degradación) en vez de romper el prerender — la
  // pantalla igual los carga en runtime del lado del cliente.
  const plans = await container.getPricingPlans.execute().catch(() => [])
  const sd = REGION_SD[container.region]
  const path = seoMetaFor(container.region).path
  const plansUrl = `${SITE}${path}#planes`

  const organization = {
    "@type": "Organization",
    "@id": `${SITE}/#organization`,
    name: "Wellnod",
    url: `${SITE}${path}`,
    description: sd.description,
    areaServed: { "@type": "Country", name: sd.country },
  }

  const software = {
    "@type": "SoftwareApplication",
    "@id": `${SITE}/#software`,
    name: "Wellnod",
    applicationCategory: "BusinessApplication",
    operatingSystem: "Web",
    inLanguage: sd.inLanguage,
    publisher: { "@id": `${SITE}/#organization` },
    offers: plans.map((plan) => ({
      "@type": "Offer",
      name: plan.name,
      description: plan.tagline,
      price: plan.monthlyPrice.amount,
      priceCurrency: plan.monthlyPrice.currency,
      // Etiqueta legible: "Gratis" cuando el precio es 0.
      category: formatMoney(plan.monthlyPrice),
      url: plansUrl,
    })),
  }

  const graph = {
    "@context": "https://schema.org",
    "@graph": [organization, software],
  }
  // </script> dentro del JSON cerraría la etiqueta antes de tiempo.
  return JSON.stringify(graph).replace(/</g, "\\u003c")
}
