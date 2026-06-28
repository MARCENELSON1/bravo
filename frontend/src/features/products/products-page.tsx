import { useState } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { toast } from "sonner"

import { isApiError } from "@/api/api-error"
import type { IngredientDTO, RecipeItemDTO } from "@/api/types-inventory"
import type { ProductDTO } from "@/api/types-operations"
import { FormError } from "@/components/form-error"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Field, FieldError, FieldGroup, FieldLabel } from "@/components/ui/field"
import { GradientHeading } from "@/components/ui/gradient-heading"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
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
import { useIngredients, useRecipe, useSetRecipe } from "@/hooks/use-inventory"
import { useCreateProduct, useProducts } from "@/hooks/use-products"
import { toMilesimas, UNIT_LABELS } from "@/lib/inventory"
import { formatMoney } from "@/lib/money"

const schema = z.object({
  name: z.string().min(1, "Ingresá un nombre").max(120),
  price: z
    .string()
    .min(1, "Ingresá un precio")
    .refine((v) => Number(v) > 0, "El precio debe ser mayor a 0"),
  category: z.string().max(60).optional(),
  // Where it's prepared — routes the item to the kitchen or the bar board.
  station: z.enum(["KITCHEN", "BAR"]),
})

type ProductValues = z.infer<typeof schema>

type DraftRow = { ingredient_id: string; qty: string }

// Recipe editor (opt-in): seeds local rows from the fetched recipe once both the
// recipe and the ingredient list are loaded, so no setState-in-effect is needed.
function RecipeForm({
  product,
  initialItems,
  ingredients,
  onDone,
}: {
  product: ProductDTO
  initialItems: RecipeItemDTO[]
  ingredients: IngredientDTO[]
  onDone: () => void
}) {
  const setRecipe = useSetRecipe(product.id)
  const [rows, setRows] = useState<DraftRow[]>(() =>
    initialItems.map((i) => ({ ingredient_id: i.ingredient_id, qty: String(i.qty / 1000) }))
  )

  const unitOf = (ingredientId: string) =>
    ingredients.find((i) => i.id === ingredientId)?.unit

  const addRow = () =>
    setRows((prev) => [...prev, { ingredient_id: ingredients[0]?.id ?? "", qty: "" }])
  const removeRow = (index: number) =>
    setRows((prev) => prev.filter((_, idx) => idx !== index))
  const patchRow = (index: number, patch: Partial<DraftRow>) =>
    setRows((prev) => prev.map((row, idx) => (idx === index ? { ...row, ...patch } : row)))

  const save = () => {
    const items = rows
      .filter((r) => r.ingredient_id && Number(r.qty) > 0)
      .map((r) => ({ ingredient_id: r.ingredient_id, qty: toMilesimas(r.qty) }))
    setRecipe.mutate(
      { items },
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
      {rows.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          Sin insumos. Agregá los que consume una unidad de este producto.
        </p>
      ) : null}
      {rows.map((row, index) => (
        <div key={index} className="flex items-end gap-2">
          <Select
            value={row.ingredient_id}
            onValueChange={(v) => patchRow(index, { ingredient_id: v })}
          >
            <SelectTrigger className="flex-1">
              <SelectValue placeholder="Insumo" />
            </SelectTrigger>
            <SelectContent>
              {ingredients.map((i) => (
                <SelectItem key={i.id} value={i.id}>
                  {i.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Input
            type="number"
            step="0.001"
            min={0}
            placeholder={unitOf(row.ingredient_id) ? UNIT_LABELS[unitOf(row.ingredient_id)!] : "cant."}
            value={row.qty}
            onChange={(e) => patchRow(index, { qty: e.target.value })}
            className="max-w-[7rem]"
          />
          <Button variant="ghost" size="sm" onClick={() => removeRow(index)}>
            Quitar
          </Button>
        </div>
      ))}
      <div className="flex items-center justify-between gap-2">
        <Button variant="outline" size="sm" onClick={addRow}>
          Agregar insumo
        </Button>
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
  if (recipe.isPending || ingredients.isPending) {
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

export function ProductsPage() {
  const products = useProducts()
  const createProduct = useCreateProduct()
  const [open, setOpen] = useState(false)
  const [serverError, setServerError] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ProductValues>({
    resolver: zodResolver(schema),
    defaultValues: { name: "", price: "", category: "", station: "KITCHEN" },
  })

  const onSubmit = handleSubmit((values) => {
    setServerError(null)
    createProduct.mutate(
      {
        name: values.name,
        priceAmount: Math.round(Number(values.price) * 100),
        category: values.category ? values.category : null,
        station: values.station,
      },
      {
        onSuccess: () => {
          toast.success("Producto creado.")
          reset()
          setOpen(false)
        },
        onError: (error) =>
          setServerError(isApiError(error) ? error.message : "No pudimos crear el producto."),
      }
    )
  })

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-5 px-6 py-8">
      <header className="flex items-end justify-between gap-2">
        <div className="flex flex-col gap-1">
          <GradientHeading size="md" weight="bold">
            Productos
          </GradientHeading>
          <p className="text-sm text-muted-foreground">Tu catálogo y precios.</p>
        </div>
        <Sheet open={open} onOpenChange={setOpen}>
          <SheetTrigger asChild>
            <Button>Nuevo producto</Button>
          </SheetTrigger>
          <SheetContent>
            <SheetHeader>
              <SheetTitle>Nuevo producto</SheetTitle>
              <SheetDescription>El precio se ingresa en la moneda del comercio.</SheetDescription>
            </SheetHeader>
            <form onSubmit={onSubmit} className="flex flex-col gap-4 px-4 pb-4" noValidate>
              <FieldGroup>
                <Field>
                  <FieldLabel htmlFor="name">Nombre</FieldLabel>
                  <Input id="name" aria-invalid={!!errors.name} {...register("name")} />
                  <FieldError>{errors.name?.message}</FieldError>
                </Field>
                <Field>
                  <FieldLabel htmlFor="price">Precio</FieldLabel>
                  <Input
                    id="price"
                    type="number"
                    step="0.01"
                    inputMode="decimal"
                    aria-invalid={!!errors.price}
                    {...register("price")}
                  />
                  <FieldError>{errors.price?.message}</FieldError>
                </Field>
                <Field>
                  <FieldLabel htmlFor="category">Categoría (opcional)</FieldLabel>
                  <Input id="category" {...register("category")} />
                </Field>
                <Field>
                  <FieldLabel htmlFor="station">Estación</FieldLabel>
                  <select
                    id="station"
                    className="h-9 rounded-md border border-input bg-transparent px-3 text-sm shadow-xs"
                    {...register("station")}
                  >
                    <option value="KITCHEN">Cocina</option>
                    <option value="BAR">Barra</option>
                  </select>
                </Field>
              </FieldGroup>
              <FormError message={serverError} />
              <Button type="submit" disabled={createProduct.isPending}>
                {createProduct.isPending ? "Creando…" : "Crear producto"}
              </Button>
            </form>
          </SheetContent>
        </Sheet>
      </header>

      <div className="overflow-hidden rounded-xl border border-border">
        {products.isPending ? (
          <div className="flex justify-center p-10">
            <Spinner className="size-5 text-muted-foreground" />
          </div>
        ) : products.data && products.data.length > 0 ? (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Nombre</TableHead>
                <TableHead>Categoría</TableHead>
                <TableHead>Estación</TableHead>
                <TableHead className="text-right">Precio</TableHead>
                <TableHead className="text-right">Estado</TableHead>
                <TableHead className="text-right">Receta</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {products.data.map((p) => (
                <TableRow key={p.id}>
                  <TableCell className="font-medium">{p.name}</TableCell>
                  <TableCell className="text-muted-foreground">{p.category ?? "—"}</TableCell>
                  <TableCell className="text-muted-foreground">
                    {p.station === "BAR" ? "Barra" : "Cocina"}
                  </TableCell>
                  <TableCell className="text-right tabular-nums">
                    {formatMoney(p.price_amount, p.currency)}
                  </TableCell>
                  <TableCell className="text-right">
                    <Badge variant={p.active ? "default" : "secondary"}>
                      {p.active ? "Activo" : "Inactivo"}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right">
                    <RecipeSheet product={p} />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        ) : (
          <p className="p-8 text-center text-sm text-muted-foreground">
            Todavía no cargaste productos.
          </p>
        )}
      </div>
    </div>
  )
}
