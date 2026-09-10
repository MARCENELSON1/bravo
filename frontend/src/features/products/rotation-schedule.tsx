import { useTranslation } from "react-i18next"

import { GlassCard } from "@/components/ui/glass-card"
import { Spinner } from "@/components/ui/spinner"
import { useProductRotation } from "@/hooks/use-products"
import { type RangeWindow } from "@/lib/finance-range"
import { formatMoney } from "@/lib/money"

// Rotación por día de semana (Productos v2 Tanda B): qué días vendés más y cuál es
// el plato estrella de cada día, a partir de sale_facts.
//
// Dos formas para el mismo dato, porque siete días caben distinto según el ancho:
//
//   - Ancho: siete columnas, una por día, con la barra parada. Es la forma natural de
//     una semana —se lee de lunes a domingo de un vistazo— y deja la tarjeta baja, que
//     es lo que hace falta cuando comparte fila con otra.
//   - Angosto: una fila por día con la barra acostada. En siete columnas de cuarenta
//     píxeles no entra ni el importe.
//
// Los dos dibujan la misma lista; lo que cambia es hacia dónde crece la barra.
export function RotationSchedule({ period }: { period: RangeWindow }) {
  const { t } = useTranslation()
  const weekdays = t("products.weekdays", { returnObjects: true }) as unknown as string[]
  const rotation = useProductRotation({ from: period.from, to: period.to })

  if (rotation.isPending) {
    return (
      <GlassCard className="flex justify-center p-10">
        <Spinner className="size-5 text-muted-foreground" />
      </GlassCard>
    )
  }
  if (!rotation.data) {
    return (
      <GlassCard className="p-6 text-sm text-muted-foreground">
        {t("products.rotation.error")}
      </GlassCard>
    )
  }

  const { currency, rows } = rotation.data
  const maxUnits = Math.max(1, ...rows.map((r) => r.units))
  const hasSales = rows.some((r) => r.units > 0)
  const share = (units: number) => `${Math.round((units / maxUnits) * 100)}%`

  return (
    <GlassCard className="flex flex-col gap-4 p-6">
      <header className="flex flex-col gap-1">
        <h2 className="text-base font-semibold text-foreground">{t("products.rotation.title")}</h2>
        <p className="text-sm text-muted-foreground">
          {t("products.rotation.subtitle")}
        </p>
      </header>

      {!hasSales ? (
        <p className="text-sm text-muted-foreground">
          {t("products.rotation.noSales")}
        </p>
      ) : (
        <>
          {/* Ancho: la semana en siete columnas. La barra crece hacia arriba dentro de
              una caja de alto fijo — un porcentaje necesita medirse contra algo, y si
              el padre creciera con su contenido no habría contra qué. */}
          <ul className="hidden grid-cols-7 gap-2 md:grid lg:gap-3">
            {rows.map((r) => (
              <li key={r.weekday} className="flex min-w-0 flex-col items-center gap-2">
                <div className="flex h-24 w-full items-end">
                  <div
                    className="w-full rounded-t-md bg-foreground/25"
                    style={{ height: share(r.units) }}
                  />
                </div>
                <span className="text-xs font-medium text-muted-foreground">
                  {weekdays[r.weekday] ?? "?"}
                </span>
                <span className="text-xs tabular-nums text-foreground">
                  {formatMoney(r.sales_amount, currency)}
                </span>
                <span
                  title={r.top_product_name ?? undefined}
                  className="w-full truncate text-center text-[11px] text-muted-foreground"
                >
                  {r.top_product_name ?? "—"}
                </span>
              </li>
            ))}
          </ul>

          {/* Angosto: un día por renglón, con la barra acostada. */}
          <ul className="flex flex-col gap-2 md:hidden">
            {rows.map((r) => (
              <li key={r.weekday} className="flex items-center gap-3">
                <span className="w-9 shrink-0 text-xs font-medium text-muted-foreground">
                  {weekdays[r.weekday] ?? "?"}
                </span>
                <div className="h-6 min-w-0 flex-1 overflow-hidden rounded-md bg-foreground/5">
                  <div
                    className="h-full rounded-md bg-foreground/25"
                    style={{ width: share(r.units) }}
                  />
                </div>
                <span className="w-20 shrink-0 truncate text-right text-xs text-muted-foreground">
                  {r.top_product_name ?? "—"}
                </span>
                <span className="min-w-24 shrink-0 text-right text-sm tabular-nums text-foreground">
                  {formatMoney(r.sales_amount, currency)}
                </span>
              </li>
            ))}
          </ul>
        </>
      )}
    </GlassCard>
  )
}
