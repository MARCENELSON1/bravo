import { useTranslation } from "react-i18next"

import { setLanguage, SUPPORTED_LANGS, type Lang } from "@/i18n"
import { cn } from "@/lib/utils"

const LABEL: Record<Lang, string> = { es: "ES", en: "EN" }

// Selector de idioma ES/EN (persiste en localStorage). Default español → un
// restaurante US lo pasa a English y se recuerda.
export function LanguageSwitcher({ className }: { className?: string }) {
  const { t, i18n } = useTranslation()
  const current: Lang = i18n.language?.startsWith("en") ? "en" : "es"
  return (
    <div
      role="group"
      aria-label={t("common.language")}
      className={cn(
        "inline-flex items-center gap-0.5 rounded-full border border-border p-0.5",
        className
      )}
    >
      {SUPPORTED_LANGS.map((lang) => {
        const active = current === lang
        return (
          <button
            key={lang}
            type="button"
            onClick={() => setLanguage(lang)}
            aria-pressed={active}
            className={cn(
              "rounded-full px-2.5 py-1 text-xs font-medium transition duration-200 ease-out",
              active
                ? "bg-foreground text-background"
                : "text-muted-foreground hover:text-foreground"
            )}
          >
            {LABEL[lang]}
          </button>
        )
      })}
    </div>
  )
}
