// Fundación i18n (Fase 1 internacionalización). Init síncrono con recursos inline
// (sin backend, sin suspense). Default: español → paridad total (ningún usuario
// actual ve un cambio). Un restaurante US togglea a English (se recuerda).
import i18n from "i18next"
import { initReactI18next } from "react-i18next"

import { en } from "@/i18n/locales/en"
import { es } from "@/i18n/locales/es"

export type Lang = "es" | "en"
export const SUPPORTED_LANGS: Lang[] = ["es", "en"]
export const LANG_STORAGE_KEY = "wellnod:lang"

/**
 * Idioma inicial en la entrada pública (pre-login), por prioridad:
 *   1. Elección explícita del usuario (persistida) → gana siempre.
 *   2. Navegador en inglés (`en-*`) → inglés (un usuario US entra y ve inglés).
 *   3. Cualquier otro caso → español (paridad; AR y navegadores desconocidos).
 * (Adentro de la app, cuando se exponga, mandará el `locale` del tenant.)
 * Función pura para poder testearla sin tocar el navegador.
 */
export function pickInitialLang(saved: string | null, browserLang: string | undefined): Lang {
  if (saved === "es" || saved === "en") return saved
  if ((browserLang ?? "").toLowerCase().startsWith("en")) return "en"
  return "es"
}

function initialLang(): Lang {
  let saved: string | null = null
  try {
    saved = localStorage.getItem(LANG_STORAGE_KEY)
  } catch {
    // storage no disponible
  }
  let browserLang: string | undefined
  try {
    browserLang = navigator.language
  } catch {
    // navigator no disponible
  }
  return pickInitialLang(saved, browserLang)
}

void i18n.use(initReactI18next).init({
  resources: {
    es: { translation: es },
    en: { translation: en },
  },
  lng: initialLang(),
  fallbackLng: "es",
  interpolation: { escapeValue: false }, // React ya escapa
  react: { useSuspense: false },
})

export function setLanguage(lang: Lang): void {
  try {
    localStorage.setItem(LANG_STORAGE_KEY, lang)
  } catch {
    // ignoramos: igual cambiamos el idioma en memoria
  }
  void i18n.changeLanguage(lang)
}

export default i18n
