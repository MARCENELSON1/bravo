import i18n from "@/i18n"

// Locale para formatear FECHAS, HORAS y NÚMEROS según el idioma activo de la UI:
//   es → "es-AR" (24h, DD/MM, "1,5")   ·   en → "en-US" (12h, MM/DD, "1.5").
// Default "es-AR" → paridad: un usuario AR ve exactamente el formato de antes.
//
// OJO: el formato de MONTOS NO pasa por acá — vive en `lib/money.ts` y sigue la
// MONEDA, no el idioma (un importe en ARS siempre se muestra "$1.234,56", aunque
// la UI esté en inglés).
function uiLocale(): string {
  return i18n.language?.startsWith("en") ? "en-US" : "es-AR"
}

// Fechas/horas y números comparten el locale de la UI; se exponen con dos nombres
// por claridad en el call-site.
export const dateLocale = uiLocale
export const numberLocale = uiLocale
