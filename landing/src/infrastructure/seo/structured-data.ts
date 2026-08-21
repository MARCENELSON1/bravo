/**
 * JSON-LD para motores de búsqueda y de respuesta.
 *
 * Se genera en tiempo de build desde los MISMOS repositorios que alimentan la
 * pantalla. Escrito a mano se desincronizaría: cambiás un precio en el
 * repositorio y el structured data seguiría diciendo el viejo. Así no puede pasar.
 */
import type { Container } from "@/infrastructure/di/container"
import { formatMoney } from "@/domain/value-objects/money"

const SITE = "https://wellnod.com"

export async function buildStructuredData(container: Container): Promise<string> {
  const [plans, content] = await Promise.all([
    container.getPricingPlans.execute(),
    container.getLandingContent.execute(),
  ])
  const faqs = content.faqs

  const organization = {
    "@type": "Organization",
    "@id": `${SITE}/#organization`,
    name: "Wellnod",
    url: SITE,
    description:
      "Sistema de gestión para restaurantes, bares y cafés: comandas digitales, " +
      "cobros, facturación electrónica y copiloto de IA en español.",
    areaServed: { "@type": "Country", name: "Argentina" },
  }

  const software = {
    "@type": "SoftwareApplication",
    "@id": `${SITE}/#software`,
    name: "Wellnod",
    applicationCategory: "BusinessApplication",
    operatingSystem: "Web",
    inLanguage: "es-AR",
    publisher: { "@id": `${SITE}/#organization` },
    offers: plans.map((plan) => ({
      "@type": "Offer",
      name: plan.name,
      description: plan.tagline,
      price: plan.monthlyPrice.amount,
      priceCurrency: plan.monthlyPrice.currency,
      // Etiqueta legible: "Gratis" cuando el precio es 0.
      category: formatMoney(plan.monthlyPrice),
      url: `${SITE}/#planes`,
    })),
  }

  // Lo que más citan los motores de respuesta: preguntas con su respuesta textual.
  const faqPage = {
    "@type": "FAQPage",
    "@id": `${SITE}/#faq`,
    mainEntity: faqs.map((faq) => ({
      "@type": "Question",
      name: faq.question,
      acceptedAnswer: { "@type": "Answer", text: faq.answer },
    })),
  }

  const graph = {
    "@context": "https://schema.org",
    "@graph": [organization, software, faqPage],
  }
  // </script> dentro del JSON cerraría la etiqueta antes de tiempo.
  return JSON.stringify(graph).replace(/</g, "\\u003c")
}
