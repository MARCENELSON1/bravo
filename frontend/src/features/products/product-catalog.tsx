import { useMemo, useState } from "react"
import { toast } from "sonner"
import { useTranslation } from "react-i18next"

import { apiErrorText } from "@/api/translate-error"
import type { IngredientDTO, PreparationDTO, RecipeItemDTO } from "@/api/types-inventory"
import type { ProductDTO } from "@/api/types-operations"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { EmptyState } from "@/components/ui/empty-state"
import { Input } from "@/components/ui/input"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet"
import { Spinner } from "@/components/ui/spinner"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  catalogCategories,
  type CatalogStatus,
  filterCatalog,
  mergeCatalogRows,
} from "@/features/products/catalog-rows"
import { ComponentRowsEditor } from "@/features/products/preparations-manager"
import { ModifiersSheet } from "@/features/products/modifiers-editor"
import { ProductFicha } from "@/features/products/product-ficha"
import {
  type ComponentDraft,
  draftsToItems,
  itemsToDrafts,
} from "@/features/products/recipe-items"
import { useProductPerformance } from "@/hooks/use-analytics"
import {
  useFoodCost,
  useIngredients,
  usePreparations,
  useRecipe,
  useSetRecipe,
} from "@/hooks/use-inventory"
import { useProducts } from "@/hooks/use-products"
import { type RangeWindow } from "@/lib/finance-range"
import { formatMoney } from "@/lib/money"

// Recipe editor (opt-in): seeds local rows from the fetched recipe once the
// recipe, ingredients and preparations are loaded (no setState-in-effect). Un
// ítem puede ser un insumo o una preparación (receta madre).
function RecipeForm({
  product,
  initialItems,
  ingredients,
  preparations,
  onDone,
}: {
  product: ProductDTO
  initialItems: RecipeItemDTO[]
  ingredients: IngredientDTO[]
  preparations: PreparationDTO[]
  onDone: () => void
}) {
  const { t } = useTranslation()
  const setRecipe = useSetRecipe(product.id)
  const [rows, setRows] = useState<ComponentDraft[]>(() => itemsToDrafts(initialItems))

  const save = () => {
    setRecipe.mutate(
      { items: draftsToItems(rows) },
      {
        onSuccess: () => {
          toast.success(t("products.recipe.saved"))
          onDone()
        },
        onError: (error) =>
          toast.error(apiErrorText(error, t, t("products.recipe.saveError"))),
      }
    )
  }

  if (ingredients.length === 0) {
    return (
      <p className="px-4 py-6 text-sm text-muted-foreground">
        {t("products.recipe.noIngredients")}
      </p>
    )
  }

  return (
    <div className="flex flex-col gap-3 px-4 pb-4">
      <ComponentRowsEditor
        rows={rows}
        onChange={setRows}
        ingredients={ingredients}
        preparations={preparations}
      />
      <div className="flex items-center justify-end">
        <Button onClick={save} disabled={setRecipe.isPending}>
          {setRecipe.isPending ? t("products.actions.saving") : t("products.recipe.save")}
        </Button>
      </div>
    </div>
  )
}

function RecipeEditor({ product, onDone }: { product: ProductDTO; onDone: () => void }) {
  const recipe = useRecipe(product.id)
  const ingredients = useIngredients()
  const preparations = usePreparations()
  if (recipe.isPending || ingredients.isPending || preparations.isPending) {
    return (
      <div className="flex justify-center p-10">
        <Spinner className="size-5 text-muted-foreground" />
      </div>
    )
  }
  return (
    <RecipeForm
      product={product}
      initialItems={recipe.data?.items ?? []}
      ingredients={ingredients.data ?? []}
      preparations={preparations.data ?? []}
      onDone={onDone}
    />
  )
}

function RecipeSheet({ product }: { product: ProductDTO }) {
  const { t } = useTranslation()
  const [open, setOpen] = useState(false)
  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button variant="ghost" size="sm">
          {t("products.recipe.button")}
        </Button>
      </SheetTrigger>
      <SheetContent>
        <SheetHeader>
          <SheetTitle>{t("products.recipe.sheetTitle", { name: product.name })}</SheetTitle>
          <SheetDescription>
            {t("products.recipe.sheetDescription")}
          </SheetDescription>
        </SheetHeader>
        {open ? <RecipeEditor product={product} onDone={() => setOpen(false)} /> : null}
      </SheetContent>
    </Sheet>
  )
}

// Catálogo (Productos v3 Fase 1): cruza productos + food cost + vendidos del
// período, con buscador y filtros. Es la tabla que sirve para decidir.
export function ProductCatalog({ period }: { period: RangeWindow }) {
  const { t } = useTranslation()
  const products = useProducts()
  const foodCost = useFoodCost()
  const perfQuery = useMemo(
    // limit alto: la columna "Vendidos" no debe truncarse por ranking de ventas.
    () => ({ from: period.from, to: period.to, limit: 1000 }),
    [period]
  )
  const perf = useProductPerformance(perfQuery)

  const [q, setQ] = useState("")
  const [category, setCategory] = useState("")
  const [status, setStatus] = useState<CatalogStatus>("all")

  const rows = useMemo(
    () => mergeCatalogRows(products.data ?? [], foodCost.data?.rows ?? [], perf.data ?? []),
    [products.data, foodCost.data, perf.data]
  )
  const categories = useMemo(() => catalogCategories(products.data ?? []), [products.data])
  const filtered = useMemo(
    () => filterCatalog(rows, { q, category, status }),
    [rows, q, category, status]
  )
  const currency = foodCost.data?.currency ?? products.data?.[0]?.currency ?? "ARS"

  return (
    <section className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center gap-2">
        <h2 className="text-sm font-semibold text-foreground">{t("products.catalog.title")}</h2>
        <div className="ml-auto flex flex-wrap items-center gap-2">
          <Input
            placeholder={t("products.catalog.searchPlaceholder")}
            value={q}
            onChange={(e) => setQ(e.target.value)}
            className="h-9 w-full sm:w-40"
          />
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="h-9 rounded-md border border-input bg-transparent px-3 text-sm shadow-xs"
          >
            <option value="">{t("products.catalog.allCategories")}</option>
            {categories.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value as CatalogStatus)}
            className="h-9 rounded-md border border-input bg-transparent px-3 text-sm shadow-xs"
          >
            <option value="all">{t("products.catalog.statusAll")}</option>
            <option value="active">{t("products.catalog.statusActive")}</option>
            <option value="inactive">{t("products.catalog.statusInactive")}</option>
          </select>
        </div>
      </div>

      <div className="overflow-hidden rounded-xl border border-border">
        {products.isPending ? (
          <div className="flex justify-center p-10">
            <Spinner className="size-5 text-muted-foreground" />
          </div>
        ) : filtered.length > 0 ? (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t("products.catalog.columns.name")}</TableHead>
                  <TableHead>{t("products.catalog.columns.category")}</TableHead>
                  <TableHead>{t("products.catalog.columns.station")}</TableHead>
                  <TableHead className="text-right">{t("products.catalog.columns.price")}</TableHead>
                  <TableHead className="text-right">{t("products.catalog.columns.cost")}</TableHead>
                  <TableHead className="text-right">{t("products.catalog.columns.leaves")}</TableHead>
                  <TableHead className="text-right">{t("products.catalog.columns.sold")}</TableHead>
                  <TableHead className="text-right">{t("products.catalog.columns.status")}</TableHead>
                  <TableHead className="text-right">{t("products.catalog.columns.recipe")}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.map((row) => {
                  const p = row.product
                  return (
                    <TableRow key={p.id}>
                      <TableCell className="font-medium">
                        {p.name}
                        {row.cost !== null && !row.ratioSane ? (
                          <Badge
                            variant="outline"
                            className="ml-2 align-middle text-xs font-normal text-warning"
                            title={t("products.catalog.incompleteRecipeTitle")}
                          >
                            {t("products.badges.incompleteRecipe")}
                          </Badge>
                        ) : null}
                        {row.cost !== null && !row.costConfirmed ? (
                          <Badge
                            variant="secondary"
                            className="ml-2 align-middle text-xs font-normal"
                            title={
                              row.coverageBps !== null
                                ? t("products.catalog.estimatedTitle", {
                                    pct: Math.round(row.coverageBps / 100),
                                  })
                                : undefined
                            }
                          >
                            {t("products.badges.estimated")}
                          </Badge>
                        ) : null}
                      </TableCell>
                      <TableCell className="text-muted-foreground">{p.category ?? "—"}</TableCell>
                      <TableCell className="text-muted-foreground">
                        {p.station === "BAR"
                          ? t("products.catalog.stationBar")
                          : t("products.catalog.stationKitchen")}
                      </TableCell>
                      <TableCell className="text-right tabular-nums">
                        {formatMoney(p.price_amount, p.currency)}
                      </TableCell>
                      <TableCell className="text-right tabular-nums text-muted-foreground">
                        {row.cost === null ? "—" : formatMoney(row.cost, currency)}
                      </TableCell>
                      <TableCell className="text-right tabular-nums">
                        {row.margin === null ? (
                          "—"
                        ) : (
                          <span
                            className={
                              row.costConfirmed && row.ratioSane
                                ? "font-medium"
                                : "text-muted-foreground"
                            }
                          >
                            {formatMoney(row.margin, currency)}
                            {row.marginBps !== null ? (
                              <span className="ml-1 text-xs text-muted-foreground">
                                {Math.round(row.marginBps / 100)}%
                              </span>
                            ) : null}
                          </span>
                        )}
                      </TableCell>
                      <TableCell className="text-right tabular-nums">{row.units}</TableCell>
                      <TableCell className="text-right">
                        <Badge variant={p.active ? "default" : "secondary"}>
                          {p.active ? t("products.catalog.active") : t("products.catalog.inactive")}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-1">
                          <ProductFicha product={p} period={period} />
                          <RecipeSheet product={p} />
                          <ModifiersSheet product={p} />
                        </div>
                      </TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          </div>
        ) : (
          <EmptyState>
            {products.data && products.data.length > 0
              ? t("products.catalog.noMatch")
              : t("products.catalog.empty")}
          </EmptyState>
        )}
      </div>

      <p className="mt-2 text-xs text-muted-foreground">
        <span className="font-medium">{t("products.catalog.footnote.price")}</span>
        {t("products.catalog.footnote.afterPrice")}
        <span className="font-medium">{t("products.catalog.footnote.leaves")}</span>
        {t("products.catalog.footnote.afterLeaves")}
        <em>{t("products.catalog.footnote.netVat")}</em>
        {t("products.catalog.footnote.afterNetVat")}
      </p>
    </section>
  )
}
