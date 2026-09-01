import { useMemo, useState } from "react"
import { useTranslation } from "react-i18next"

import type { ProductDTO, Station } from "@/api/types-operations"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { cn } from "@/lib/utils"
import { formatMoney } from "@/lib/money"
import { splitCategory } from "@/lib/menu-tree"
import { getUsage, rankProducts } from "@/lib/product-usage"

// Fast product picker, organizado por niveles para que el mozo llegue en pocos
// toques: "Frecuentes" arriba (lo que más carga, aprendido del uso) y abajo la
// carta por estación → categoría → subcategoría → producto. La subcategoría sale
// de partir `category` en "/" (ver lib/menu-tree). Escribir en el buscador puentea
// la jerarquía y devuelve resultados planos, como antes.
const ALL = "__all__"
const UNCATEGORIZED = "__none__"
const NO_SUB = "__nosub__"

// Una tarjeta de producto. `big` la usa la fila de Frecuentes: mismo contenido,
// área de toque más grande.
function ProductCard({
  product,
  onAdd,
  big,
}: {
  product: ProductDTO
  onAdd: (product: ProductDTO) => void
  big?: boolean
}) {
  return (
    <button
      type="button"
      onClick={() => onAdd(product)}
      className={cn(
        "flex flex-col items-start justify-between gap-1 rounded-lg border bg-card p-3 text-left transition hover:border-primary hover:bg-accent active:scale-[0.98]",
        big ? "min-h-20 border-primary/30 bg-primary/5" : "min-h-16"
      )}
    >
      <span className={cn("font-medium leading-tight", big ? "text-base" : "text-sm")}>
        {product.name}
      </span>
      <span className="text-xs text-muted-foreground">
        {formatMoney(product.price_amount, product.currency)}
      </span>
    </button>
  )
}

// Fila de chips (estaciones o categorías). Scrollea en horizontal si no entran.
function ChipRow({
  label,
  options,
  value,
  onChange,
}: {
  label: string
  options: { value: string; label: string }[]
  value: string
  onChange: (value: string) => void
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <span className="text-xs text-muted-foreground">{label}</span>
      <div className="flex gap-2 overflow-x-auto pb-1">
        {options.map((o) => (
          <button
            key={o.value}
            type="button"
            aria-pressed={o.value === value}
            onClick={() => onChange(o.value)}
            className={cn(
              "h-9 shrink-0 rounded-lg border px-3 text-sm transition-colors active:scale-[0.98]",
              o.value === value
                ? "border-primary bg-primary/10 font-medium text-foreground"
                : "border-border text-muted-foreground hover:bg-accent hover:text-foreground"
            )}
          >
            {o.label}
          </button>
        ))}
      </div>
    </div>
  )
}

export function ProductGrid({
  products,
  onAdd,
}: {
  products: ProductDTO[]
  onAdd: (product: ProductDTO, quantity: number) => void
}) {
  const { t } = useTranslation()
  const [search, setSearch] = useState("")
  const [qty, setQty] = useState(1)
  const [station, setStation] = useState<string>(ALL)
  const [category, setCategory] = useState<string>(ALL)
  const [subcategory, setSubcategory] = useState<string>(ALL)

  const usage = useMemo(() => getUsage(), [])
  // Todos los activos, más usados primero (la misma regla de siempre).
  const ranked = useMemo(() => rankProducts(products, "", usage), [products, usage])
  // Resultados de búsqueda: planos, sin jerarquía.
  const found = useMemo(() => rankProducts(products, search, usage), [products, search, usage])
  const searching = search.trim() !== ""

  // Nivel 1 — estaciones presentes. Con una sola, la fila no aparece.
  const stations = useMemo(() => {
    const present = new Set<Station>()
    ranked.forEach((p) => present.add(p.station))
    return (["KITCHEN", "BAR"] as Station[]).filter((s) => present.has(s))
  }, [ranked])

  const inStation = useMemo(
    () => (station === ALL ? ranked : ranked.filter((p) => p.station === station)),
    [ranked, station]
  )

  // Nivel 2 — categorías dentro de la estación elegida, alfabéticas. Los productos
  // sin categoría se agrupan al final en vez de perderse.
  const categories = useMemo(() => {
    const named = new Set<string>()
    let hasUncategorized = false
    inStation.forEach((p) => {
      const { main } = splitCategory(p.category)
      if (main) named.add(main)
      else hasUncategorized = true
    })
    const list = [...named].sort((a, b) => a.localeCompare(b))
    return hasUncategorized ? [...list, UNCATEGORIZED] : list
  }, [inStation])

  const inCategory = useMemo(() => {
    if (category === ALL) return inStation
    if (category === UNCATEGORIZED)
      return inStation.filter((p) => splitCategory(p.category).main === null)
    return inStation.filter((p) => splitCategory(p.category).main === category)
  }, [inStation, category])

  // Nivel 3 — subcategorías de la categoría elegida. Solo tiene sentido con una
  // categoría concreta seleccionada: en "Todos" se mezclarían las de todas.
  const subcategories = useMemo(() => {
    if (category === ALL || category === UNCATEGORIZED) return []
    const named = new Set<string>()
    let hasBare = false
    inCategory.forEach((p) => {
      const { sub } = splitCategory(p.category)
      if (sub) named.add(sub)
      else hasBare = true
    })
    if (named.size === 0) return []
    const list = [...named].sort((a, b) => a.localeCompare(b))
    return hasBare ? [...list, NO_SUB] : list
  }, [inCategory, category])

  // Nivel 4 — los productos que quedan.
  const visible = useMemo(() => {
    if (subcategory === ALL) return inCategory
    if (subcategory === NO_SUB)
      return inCategory.filter((p) => splitCategory(p.category).sub === null)
    return inCategory.filter((p) => splitCategory(p.category).sub === subcategory)
  }, [inCategory, subcategory])

  // Los más cargados en este dispositivo. Sin historial todavía, la fila se omite
  // (mostrar seis productos al azar como "frecuentes" sería mentir).
  const frequent = useMemo(() => ranked.filter((p) => (usage[p.id] ?? 0) > 0).slice(0, 6), [
    ranked,
    usage,
  ])

  const add = (product: ProductDTO) => {
    onAdd(product, qty)
    setQty(1) // reset to the common case after each add
  }

  const pickStation = (value: string) => {
    setStation(value)
    setCategory(ALL) // la categoría anterior puede no existir en la nueva estación
    setSubcategory(ALL)
  }

  const pickCategory = (value: string) => {
    setCategory(value)
    setSubcategory(ALL)
  }

  const grid = (list: ProductDTO[]) =>
    list.length > 0 ? (
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
        {list.map((p) => (
          <ProductCard key={p.id} product={p} onAdd={add} />
        ))}
      </div>
    ) : (
      <p className="text-sm text-muted-foreground">{t("orders.noProducts")}</p>
    )

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-2">
        <Input
          placeholder={t("orders.searchProduct")}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="flex-1"
        />
        <div className="flex items-center gap-1">
          <Button
            variant="outline"
            className="h-11 w-11 p-0 text-lg"
            onClick={() => setQty((q) => Math.max(1, q - 1))}
            aria-label={t("orders.lessQuantity")}
          >
            −
          </Button>
          <span className="w-7 text-center text-sm font-medium tabular-nums">{qty}</span>
          <Button
            variant="outline"
            className="h-11 w-11 p-0 text-lg"
            onClick={() => setQty((q) => q + 1)}
            aria-label={t("orders.moreQuantity")}
          >
            +
          </Button>
        </div>
      </div>

      {searching ? (
        grid(found)
      ) : (
        <>
          {frequent.length > 0 ? (
            <section className="flex flex-col gap-2">
              <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                {t("orders.picker.frequent")}
              </span>
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
                {frequent.map((p) => (
                  <ProductCard key={p.id} product={p} onAdd={add} big />
                ))}
              </div>
            </section>
          ) : null}

          {stations.length > 1 ? (
            <ChipRow
              label={t("orders.picker.station")}
              value={station}
              onChange={pickStation}
              options={[
                { value: ALL, label: t("orders.picker.all") },
                ...stations.map((s) => ({
                  value: s,
                  label: t(`orders.picker.stationLabels.${s}`),
                })),
              ]}
            />
          ) : null}

          {categories.length > 1 ? (
            <ChipRow
              label={t("orders.picker.category")}
              value={category}
              onChange={pickCategory}
              options={[
                { value: ALL, label: t("orders.picker.all") },
                ...categories.map((c) => ({
                  value: c,
                  label: c === UNCATEGORIZED ? t("orders.picker.uncategorized") : c,
                })),
              ]}
            />
          ) : null}

          {subcategories.length > 0 ? (
            <ChipRow
              label={t("orders.picker.subcategory")}
              value={subcategory}
              onChange={setSubcategory}
              options={[
                { value: ALL, label: t("orders.picker.all") },
                ...subcategories.map((c) => ({
                  value: c,
                  label: c === NO_SUB ? t("orders.picker.uncategorizedSub") : c,
                })),
              ]}
            />
          ) : null}

          {grid(visible)}
        </>
      )}
    </div>
  )
}
