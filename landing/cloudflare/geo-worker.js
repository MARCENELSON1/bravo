/**
 * Cloudflare Worker — ruteo geo de la landing (Fase C de la internacionalización).
 *
 * Objetivo: un visitante de EE.UU. (o del resto del mundo) ve la versión inglés/USD
 * en /en/, y uno de Argentina ve la de español/ARS en /. SIN romper SEO.
 *
 * Reglas (la #1 evita la trampa SEO clásica del geo-redirect):
 *  1) Las dos URLs (/ y /en/) se sirven DIRECTO — nunca se redirige por User-Agent.
 *     Así Googlebot (que crawlea desde US) llega a cada variante y hreflang lo guía;
 *     si redirigiéramos por IP a ciegas, indexaría solo una.
 *  2) Solo se redirige al HUMANO en la raíz "/" cuando su país ≠ AR y no eligió
 *     región antes (cookie). Todo lo demás (/en/, assets) pasa sin tocar.
 *  3) La cookie wellnod_region=ar|intl es un override explícito (selector del footer),
 *     para el caso legítimo: un argentino que quiere ver inglés, o al revés.
 *
 * Deploy: ver ./README.md.
 */

const COOKIE = "wellnod_region"

export default {
  async fetch(request) {
    const url = new URL(request.url)

    // Solo la raíz exacta entra a la decisión geo. /en/, /assets, favicon, og.png,
    // sitemap, robots, etc. pasan directo al origen (Railway).
    if (url.pathname !== "/") {
      return fetch(request)
    }

    // Override por cookie (si el visitante ya eligió región, se respeta).
    const cookie = request.headers.get("Cookie") || ""
    const chosen = /(?:^|;\s*)wellnod_region=(ar|intl)/.exec(cookie)?.[1]

    // País por IP en el edge (gratis en Cloudflare). Sin dato → AR por defecto.
    const country = request.cf && request.cf.country ? request.cf.country : "AR"
    const region = chosen || (country === "AR" ? "ar" : "intl")

    // Al humano del resto del mundo lo mandamos a la variante inglés. Los bots
    // igual pueden crawlear "/" y "/en/" directo (esto no los frena: solo un 302
    // del navegador humano, guiado por país, no por User-Agent).
    if (region === "intl") {
      url.pathname = "/en/"
      return Response.redirect(url.toString(), 302)
    }

    return fetch(request)
  },
}

// Nota: para persistir la elección del footer, la página setea el cookie
// `wellnod_region` en el cliente; este Worker solo lo LEE (no lo escribe), así el
// 302 queda cacheable por país y el override es del lado del visitante.
export { COOKIE }
