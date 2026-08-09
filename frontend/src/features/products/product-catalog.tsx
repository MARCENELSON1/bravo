import { useMemo, useState } from "react"
import { toast } from "sonner"

import { isApiError } from "@/api/api-error"
import type { IngredientDTO, PreparationDTO, RecipeItemDTO } from "@/api/types-inventory"
import type { ProductDTO } from "@/api/types-operations"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
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
  const setRecipe = useSetRecipe(product.id)
  const [rows, setRows] = useState<ComponentDraft[]>(() => itemsToDrafts(initialItems))

  const save = () => {
    setRecipe.mutate(
      { items: draftsToItems(rows) },
      {
        onSuccess: () => {
          toast.success("Receta guardada.")
          onDone()
        },
        onError: (error) =>
          toast.error(isApiError(error) ? error.message : "No pudimos guardar la receta."),
      }
    )
  }

  if (ingredients.length === 0) {
    return (
      <p className="px-4 py-6 text-sm text-muted-foreground">
        Cargá insumos en Stock antes de armar la receta.
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
          {setRecipe.isPending ? "Guardando…" : "Guardar receta"}
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
  const [open, setOpen] = useState(false)
  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button variant="ghost" size="sm">
          Receta
        </Button>
      </SheetTrigger>
      <SheetContent>
        <SheetHeader>
          <SheetTitle>Receta de {product.name}</SheetTitle>
          <SheetDescription>
            Opcional. Lo que se descuenta de stock por cada unidad vendida.
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
        <h2 className="text-sm font-semibold text-foreground">Catálogo</h2>
        <div className="ml-auto flex flex-wrap items-center gap-2">
          <Input
            placeholder="Buscar…"
            value={q}
            onChange={(e) => setQ(e.target.value)}
            className="h-9 w-40"
          />
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="h-9 rounded-md border border-input bg-transparent px-3 text-sm shadow-xs"
          >
            <option value="">Todas las categorías</option>
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
            <option value="all">Todos</option>
            <option value="active">Activos</option>
            <option value="inactive">Inactivos</option>
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
                  <TableHead>Nombre</TableHead>
                  <TableHead>Categoría</TableHead>
                  <TableHead>Estación</TableHead>
                  <TableHead className="text-right">Precio</TableHead>
                  <TableHead className="text-right">Costo</TableHead>
                  <TableHead className="text-right">Te deja</TableHead>
                  <TableHead className="text-right">Vendidos</TableHead>
                  <TableHead className="text-right">Estado</TableHead>
                  <TableHead className="text-right">Receta</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.map((row) => {
                  const p = row.product
                  return (
                    <TableRow key={p.id}>
                      <TableCell className="font-medium">{p.name}</TableCell>
                      <TableCell className="text-muted-foreground">{p.category ?? "—"}</TableCell>
                      <TableCell className="text-muted-foreground">
                        {p.station === "BAR" ? "Barra" : "Cocina"}
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
                          <span className="font-medium">
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
                          {p.active ? "Activo" : "Inactivo"}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <RecipeSheet product={p} />
                      </TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          </div>
        ) : (
          <p className="p-8 text-center text-sm text-muted-foreground">
            {products.data && products.data.length > 0
              ? "Ningún producto coincide con el filtro."
              : "Todavía no cargaste productos."}
          </p>
        )}
      </div>
    </section>
  )
}
