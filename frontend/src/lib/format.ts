import i18n from "@/i18n"

// Locale para formatear FECHAS, HORAS y NÚMEROS según el idioma activo de la UI:
//   es → "es-AR" (24h, DD/MM, "1,5")   ·   en → "en-US" (12h, MM/DD, "1.5").
// Las HORAS fuerzan el ciclo en español (ver `timeOptions`), porque el locale
// solo no alcanza para conseguir 24 h.
// Default "es-AR" → paridad: un usuario AR ve exactamente el formato de antes.
//
// OJO: el formato de MONTOS NO pasa por acá — vive en `lib/money.ts` y sigue la
// MONEDA, no el idioma (un importe en ARS siempre se muestra "$1.234,56", aunque
// la UI esté en inglés).
function isEnglish(): boolean {
  return i18n.language?.startsWith("en") ?? false
}

function uiLocale(): string {
  return isEnglish() ? "en-US" : "es-AR"
}

// Fechas/horas y números comparten el locale de la UI; se exponen con dos nombres
// por claridad en el call-site.
export const dateLocale = uiLocale
export const numberLocale = uiLocale

// Zona horaria efectiva del navegador, formateada como la leía la UI antes:
// "GMT−3 · Buenos Aires". No es una preferencia guardada del perfil todavía —
// es la que la app está usando de verdad para mostrar fechas y horas.
export function timeZoneLabel(): string {
  const tz = Intl.DateTimeFormat().resolvedOptions().timeZone
  const city = tz.split("/").pop()?.replace(/_/g, " ") ?? tz
  const offset =
    new Intl.DateTimeFormat(uiLocale(), { timeZone: tz, timeZoneName: "shortOffset" })
      .formatToParts(new Date())
      .find((p) => p.type === "timeZoneName")?.value ?? ""
  // Menos tipográfico (−), igual que el texto que estaba escrito a mano.
  return offset ? `${offset.replace("-", "−")} · ${city}` : city
}

// Opciones con las que la app muestra la hora. Viven acá, en un solo lugar, para
// que el reloj de la topbar y la fila "Formato de hora" de Configuración no
// puedan divergir: las dos leen de esto.
//
// El `hourCycle` en español es deliberado: ICU resuelve "es-AR" a 12 h con
// "p. m.", pero en Argentina un reloj digital se lee en 24 h. Inglés queda en
// el default del locale (12 h con AM/PM).
export function timeOptions(): Intl.DateTimeFormatOptions {
  return isEnglish()
    ? { hour: "2-digit", minute: "2-digit" }
    : { hour: "2-digit", minute: "2-digit", hourCycle: "h23" }
}

// Fecha corta + hora (DD/MM HH:mm). Hereda el ciclo horario de `timeOptions`,
// así que acompaña al reloj: en español no aparece "p. m.".
export function dateTimeOptions(): Intl.DateTimeFormatOptions {
  return { day: "2-digit", month: "2-digit", ...timeOptions() }
}

// ¿12 h o 24 h? No se deduce del idioma: se pregunta al formateador real. Si el
// resultado trae "a. m."/"p. m.", es de 12.
export function hourCycleLabel(): string {
  const parts = new Intl.DateTimeFormat(uiLocale(), timeOptions()).formatToParts(new Date())
  return parts.some((p) => p.type === "dayPeriod") ? "12 h" : "24 h"
}
