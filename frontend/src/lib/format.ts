import i18n from "@/i18n"

// Locale para formatear FECHAS y HORAS según el idioma activo de la UI:
//   es → "es-AR" (24h, DD/MM)   ·   en → "en-US" (12h, MM/DD).
// Default "es-AR" → paridad: un usuario AR ve exactamente el formato de antes.
//
// OJO: el formato de MONTOS NO pasa por acá — vive en `lib/money.ts` y sigue la
// MONEDA, no el idioma (un importe en ARS siempre se muestra "$1.234,56", aunque
// la UI esté en inglés). Los números sin moneda (cantidades, %, ratios) hoy
// también quedan en es-AR (ver formatQty/formatBps/formatPct, testeados).
export function dateLocale(): string {
  return i18n.language?.startsWith("en") ? "en-US" : "es-AR"
}
