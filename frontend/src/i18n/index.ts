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

function storedLang(): Lang {
  try {
    const saved = localStorage.getItem(LANG_STORAGE_KEY)
    if (saved === "es" || saved === "en") return saved
  } catch {
    // storage no disponible: usamos el default
  }
  return "es"
}

void i18n.use(initReactI18next).init({
  resources: {
    es: { translation: es },
    en: { translation: en },
  },
  lng: storedLang(),
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
