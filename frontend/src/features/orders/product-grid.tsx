import { useMemo, useState } from "react"
import { useTranslation } from "react-i18next"
import { ChevronRight } from "lucide-react"

import type { ProductDTO, Station } from "@/api/types-operations"
import { Button } from "@/components/ui/button"
import { BackButton } from "@/components/ui/back-button"
import { Input } from "@/components/ui/input"
import { cn } from "@/lib/utils"
import { formatMoney } from "@/lib/money"
import { splitCategory } from "@/lib/menu-tree"
import { getUsage, rankProducts } from "@/lib/product-usage"

// Selector de productos, por niveles: primero la categoría, después la
// subcategoría si esa categoría tiene, y recién ahí los productos.
//
// Antes estaba todo a la vez —chips de estación, de categoría, de subcategoría y
// la grilla entera— y en un celular eso queda amontonado. Navegando se ve una
// cosa por pantalla, con áreas de toque grandes.
//
// Dos atajos se conservan: "Frecuentes" arriba de todo (lo que este dispositivo
// más carga) y el buscador, que puentea la jerarquía y devuelve resultados planos.
//
// Los nombres de las categorías son datos del local, no una lista fija: salen de
// `category`, y el segundo nivel de partir ese texto en "/" (ver lib/menu-tree).
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

// Tarjeta de un grupo (categoría o subcategoría) con cuántos productos tiene
// adentro. El contador evita el pozo de entrar y encontrar dos ítems.
function GroupCard({
  label,
  count,
  onOpen,
}: {
  label: string
  count: number
  onOpen: () => void
}) {
  const { t } = useTranslation()
  return (
    <button
      type="button"
      onClick={onOpen}
      className="flex min-h-16 items-center justify-between gap-2 rounded-lg border bg-card p-3 text-left transition hover:border-primary hover:bg-accent active:scale-[0.98]"
    >
      <span className="min-w-0">
        <span className="block truncate text-sm font-medium leading-tight">{label}</span>
        <span className="text-xs text-muted-foreground">
          {t("orders.picker.itemCount", { count })}
        </span>
      </span>
      <ChevronRight className="size-4 shrink-0 text-muted-foreground" />
    </button>
  )
}

// Fila de chips. Queda solo para la estación: es un filtro, no un nivel de la
// carta. Scrollea en horizontal si no entran.
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
  // `null` = todavía no eligió, o sea que está parado en la raíz.
  const [category, setCategory] = useState<string | null>(null)
  const [subcategory, setSubcategory] = useState<string | null>(null)

  const usage = useMemo(() => getUsage(), [])
  // Todos los activos, más usados primero (la misma regla de siempre).
  const ranked = useMemo(() => rankProducts(products, "", usage), [products, usage])
  // Resultados de búsqueda: planos, sin jerarquía.
  const found = useMemo(() => rankProducts(products, search, usage), [products, search, usage])
  const searching = search.trim() !== ""

  // Estaciones presentes. Con una sola, la fila no aparece.
  const stations = useMemo(() => {
    const present = new Set<Station>()
    ranked.forEach((p) => present.add(p.station))
    return (["KITCHEN", "BAR"] as Station[]).filter((s) => present.has(s))
  }, [ranked])

  const inStation = useMemo(
    () => (station === ALL ? ranked : ranked.filter((p) => p.station === station)),
    [ranked, station]
  )

  // Nivel 1 — categorías con su conteo, alfabéticas. Los productos sin categoría
  // se agrupan al final en vez de quedar inalcanzables.
  const categories = useMemo(() => {
    const count = new Map<string, number>()
    inStation.forEach((p) => {
      const key = splitCategory(p.category).main ?? UNCATEGORIZED
      count.set(key, (count.get(key) ?? 0) + 1)
    })
    const named = [...count.keys()]
      .filter((k) => k !== UNCATEGORIZED)
      .sort((a, b) => a.localeCompare(b))
    const keys = count.has(UNCATEGORIZED) ? [...named, UNCATEGORIZED] : named
    return keys.map((key) => ({ key, count: count.get(key) ?? 0 }))
  }, [inStation])

  const inCategory = useMemo(() => {
    if (category === null) return inStation
    if (category === UNCATEGORIZED)
      return inStation.filter((p) => splitCategory(p.category).main === null)
    return inStation.filter((p) => splitCategory(p.category).main === category)
  }, [inStation, category])

  // Nivel 2 — subcategorías de la elegida. Si ningún producto usa el separador,
  // la lista queda vacía y el nivel se saltea: se va derecho a los productos.
  const subcategories = useMemo(() => {
    if (category === null || category === UNCATEGORIZED) return []
    const count = new Map<string, number>()
    inCategory.forEach((p) => {
      const key = splitCategory(p.category).sub ?? NO_SUB
      count.set(key, (count.get(key) ?? 0) + 1)
    })
    const named = [...count.keys()].filter((k) => k !== NO_SUB).sort((a, b) => a.localeCompare(b))
    if (named.length === 0) return []
    const keys = count.has(NO_SUB) ? [...named, NO_SUB] : named
    return keys.map((key) => ({ key, count: count.get(key) ?? 0 }))
  }, [inCategory, category])

  // Nivel 3 — los productos que quedan.
  const visible = useMemo(() => {
    if (subcategory === null) return inCategory
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
    setCategory(null) // la categoría anterior puede no existir en la nueva estación
    setSubcategory(null)
  }

  // Sube un nivel: de los productos a las subcategorías, o de ahí a la raíz.
  const back = () => {
    if (subcategory !== null) setSubcategory(null)
    else setCategory(null)
  }

  const nameOf = (key: string) =>
    key === UNCATEGORIZED
      ? t("orders.picker.uncategorized")
      : key === NO_SUB
        ? t("orders.picker.uncategorizedSub")
        : key

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

  // Dónde está parado y cómo volver. El botón sube un nivel; el texto de al lado
  // dice el camino, para que en la grilla de productos se sepa qué se está viendo.
  const crumb = (
    <div className="flex items-center gap-3">
      <BackButton onClick={back} label={t("orders.picker.back")} />
      <span className="min-w-0 truncate text-sm font-medium">
        {category !== null ? nameOf(category) : null}
        {subcategory !== null ? (
          <span className="text-muted-foreground"> / {nameOf(subcategory)}</span>
        ) : null}
      </span>
    </div>
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
      ) : category === null ? (
        // Raíz: frecuentes, estación y las categorías.
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

          {categories.length > 0 ? (
            <section className="flex flex-col gap-2">
              <span className="text-xs text-muted-foreground">
                {t("orders.picker.pickCategory")}
              </span>
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
                {categories.map((c) => (
                  <GroupCard
                    key={c.key}
                    label={nameOf(c.key)}
                    count={c.count}
                    onOpen={() => setCategory(c.key)}
                  />
                ))}
              </div>
            </section>
          ) : (
            <p className="text-sm text-muted-foreground">{t("orders.noProducts")}</p>
          )}
        </>
      ) : subcategories.length > 0 && subcategory === null ? (
        // Nivel del medio: esta categoría tiene subcategorías.
        <>
          {crumb}
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
            {subcategories.map((c) => (
              <GroupCard
                key={c.key}
                label={nameOf(c.key)}
                count={c.count}
                onOpen={() => setSubcategory(c.key)}
              />
            ))}
          </div>
        </>
      ) : (
        // Hoja: los productos.
        <>
          {crumb}
          {grid(visible)}
        </>
      )}
    </div>
  )
}
