import { useState } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { toast } from "sonner"

import { isApiError } from "@/api/api-error"
import type { IngredientDTO, PreparationDTO, RecipeItemDTO } from "@/api/types-inventory"
import type { ProductDTO } from "@/api/types-operations"
import { FormError } from "@/components/form-error"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Field, FieldError, FieldGroup, FieldLabel } from "@/components/ui/field"
import { GradientHeading } from "@/components/ui/gradient-heading"
import { MenuEngineering } from "@/features/products/menu-engineering-view"
import {
  ComponentRowsEditor,
  PreparationsManager,
} from "@/features/products/preparations-manager"
import {
  type ComponentDraft,
  draftsToItems,
  itemsToDrafts,
} from "@/features/products/recipe-items"
import { PricingInflationCard } from "@/features/products/pricing-inflation-card"
import { RotationSchedule } from "@/features/products/rotation-schedule"
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
  useIngredients,
  usePreparations,
  useRecipe,
  useSetRecipe,
} from "@/hooks/use-inventory"
import { useCreateProduct, useProducts } from "@/hooks/use-products"
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
    <div className="mx-auto flex w-full max-w-7xl flex-col gap-5 px-6 py-8">
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

      {/* Menu engineering (Productos v2 Tanda A): la carta clasificada. */}
      <MenuEngineering />

      {/* Productos v2 Tanda B: precios vs inflación + rotación por día. */}
      <div className="grid gap-5 lg:grid-cols-2">
        <PricingInflationCard />
        <RotationSchedule />
      </div>

      <h2 className="text-sm font-semibold text-foreground">Catálogo</h2>
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

      {/* Productos v2 Tanda C: recetas madre (preparaciones base). */}
      <PreparationsManager />
    </div>
  )
}
