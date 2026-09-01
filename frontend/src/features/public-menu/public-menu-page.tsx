import type { ReactNode } from "react"
import { useTranslation } from "react-i18next"
import { useParams } from "react-router-dom"

import { isApiError } from "@/api/api-error"
import type { PublicMenuCategoryDTO } from "@/api/public-menu-api"
import { WellnodMark } from "@/components/brand/wellnod-mark"
import { usePublicMenu } from "@/hooks/use-public-menu"
import { formatMoney } from "@/lib/money"

// Carta pública de cara al comensal (ruta /carta/:token, SIN auth). Mobile-first,
// theme-aware (sigue el tema del navegador). El token porta el tenant → sin login.
export function PublicMenuPage() {
  const { t } = useTranslation()
  const { token } = useParams<{ token: string }>()
  const { data, isLoading, isError, error } = usePublicMenu(token)

  if (isLoading) {
    return <StateScreen>{t("publicMenu.loading")}</StateScreen>
  }

  if (isError || !data) {
    // Token malformado/de otro tenant/expirado → pantalla amable "pedí el QR".
    const invalid = isApiError(error) && error.code === "invalid_table_qr_token"
    return (
      <StateScreen
        title={t(invalid ? "publicMenu.invalid.title" : "publicMenu.error.title")}
      >
        {t(invalid ? "publicMenu.invalid.body" : "publicMenu.error.body")}
      </StateScreen>
    )
  }

  const categories = data.categories.filter((c) => c.items.length > 0)

  return (
    <div className="min-h-svh bg-background text-foreground">
      <header className="sticky top-0 z-10 border-b border-border/60 bg-background/80 px-5 py-4 backdrop-blur-xl">
        <div className="mx-auto flex max-w-xl items-center gap-3">
          <WellnodMark className="h-7 w-auto shrink-0 text-foreground" />
          <div className="min-w-0">
            <h1 className="truncate text-lg font-semibold leading-tight">{data.tenant_name}</h1>
            <p className="text-xs uppercase tracking-wider text-muted-foreground">
              {t("publicMenu.menu")}
            </p>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-xl px-5 pb-16 pt-6">
        {categories.length === 0 ? (
          <StateScreen title={t("publicMenu.empty.title")} bare>
            {t("publicMenu.empty.body")}
          </StateScreen>
        ) : (
          <div className="flex flex-col gap-8">
            {categories.map((category) => (
              <MenuSection
                key={category.name ?? "__uncategorized__"}
                category={category}
                currency={data.currency}
                fallbackLabel={t("publicMenu.uncategorized")}
              />
            ))}
          </div>
        )}
      </main>

      <footer className="pb-8 text-center text-xs text-muted-foreground">
        {t("publicMenu.poweredBy")}
      </footer>
    </div>
  )
}

function MenuSection({
  category,
  currency,
  fallbackLabel,
}: {
  category: PublicMenuCategoryDTO
  currency: string
  fallbackLabel: string
}) {
  return (
    <section>
      <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
        {category.name ?? fallbackLabel}
      </h2>
      <ul className="flex flex-col divide-y divide-border/50">
        {category.items.map((item) => (
          <li key={item.id} className="flex items-baseline justify-between gap-4 py-3">
            <span className="min-w-0 text-[15px] leading-snug">{item.name}</span>
            <span className="shrink-0 tabular-nums font-medium">
              {formatMoney(item.price_amount, currency)}
            </span>
          </li>
        ))}
      </ul>
    </section>
  )
}

// Pantalla centrada para los estados (cargando / carta vacía / token inválido).
function StateScreen({
  title,
  children,
  bare = false,
}: {
  title?: string
  children: ReactNode
  bare?: boolean
}) {
  const body = (
    <div className="flex flex-col items-center gap-2 text-center">
      <WellnodMark className="mb-2 h-9 w-auto text-foreground/80" />
      {title ? <h1 className="text-lg font-semibold">{title}</h1> : null}
      <p className="max-w-xs text-sm text-muted-foreground">{children}</p>
    </div>
  )
  if (bare) return <div className="py-16">{body}</div>
  return (
    <div className="flex min-h-svh items-center justify-center bg-background px-6 text-foreground">
      {body}
    </div>
  )
}
