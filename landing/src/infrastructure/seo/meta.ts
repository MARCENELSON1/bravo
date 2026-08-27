/**
 * Metadatos SEO por región (title, description, OG, canonical, hreflang). Es la
 * ÚNICA fuente del <head> variable: el prerender inyecta `seoHead(region)` en cada
 * variante (dist/index.html es-AR · dist/en/index.html en-US). Así las dos URLs son
 * crawleables directo y hreflang le dice a Google que son la misma página en dos
 * idiomas (evita que indexe una sola).
 */
import type { Region } from "@/domain/value-objects/region"

const SITE = "https://wellnod.com"

export interface SeoMeta {
  readonly lang: string
  readonly ogLocale: string
  readonly path: string // "/" (AR) o "/en/" (INTL)
  readonly title: string
  readonly description: string
  readonly ogDescription: string
  readonly ogImage: string // ruta de la tarjeta OG por región (texto baked-in)
}

const META: Record<Region, SeoMeta> = {
  AR: {
    lang: "es",
    ogLocale: "es_AR",
    path: "/",
    title: "Wellnod · El cerebro de tu local",
    description:
      "Wellnod es el sistema todo-en-uno para tu restaurante: comandas digitales, cobros y facturación AFIP, fichaje de empleados y un copiloto de IA en español.",
    ogDescription:
      "Comandas digitales, cobros y facturación AFIP, fichaje y un copiloto de IA en español. Todo tu restaurante en una sola app.",
    ogImage: "/og.png",
  },
  INTL: {
    lang: "en",
    ogLocale: "en_US",
    path: "/en/",
    title: "Wellnod · Your restaurant's brain",
    description:
      "Wellnod is the all-in-one system for your restaurant: digital order taking, card payments with automated sales tax, employee time tracking, and an AI copilot in English.",
    ogDescription:
      "Digital order taking, card payments & automated sales tax, time tracking, and an AI copilot in English. Your whole restaurant in one app.",
    ogImage: "/og-en.png",
  },
}

export function seoMetaFor(region: Region): SeoMeta {
  return META[region]
}

function esc(s: string): string {
  return s.replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;")
}

/** Snippet HTML del <head> variable para una región. Lo inyecta el prerender. */
export function seoHead(region: Region): string {
  const m = META[region]
  const url = `${SITE}${m.path}`
  const img = `${SITE}${m.ogImage}`
  return [
    `<title>${esc(m.title)}</title>`,
    `<meta name="description" content="${esc(m.description)}" />`,
    `<link rel="canonical" href="${url}" />`,
    `<link rel="alternate" hreflang="es-AR" href="${SITE}/" />`,
    `<link rel="alternate" hreflang="en-US" href="${SITE}/en/" />`,
    `<link rel="alternate" hreflang="x-default" href="${SITE}/" />`,
    `<meta property="og:type" content="website" />`,
    `<meta property="og:site_name" content="Wellnod" />`,
    `<meta property="og:locale" content="${m.ogLocale}" />`,
    `<meta property="og:url" content="${url}" />`,
    `<meta property="og:title" content="${esc(m.title)}" />`,
    `<meta property="og:description" content="${esc(m.ogDescription)}" />`,
    `<meta property="og:image" content="${img}" />`,
    `<meta property="og:image:width" content="1200" />`,
    `<meta property="og:image:height" content="630" />`,
    `<meta property="og:image:alt" content="Wellnod" />`,
    `<meta name="twitter:card" content="summary_large_image" />`,
    `<meta name="twitter:title" content="${esc(m.title)}" />`,
    `<meta name="twitter:description" content="${esc(m.ogDescription)}" />`,
    `<meta name="twitter:image" content="${img}" />`,
  ].join("\n    ")
}
