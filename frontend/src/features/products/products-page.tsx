import { useMemo, useState } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { toast } from "sonner"

import { isApiError } from "@/api/api-error"
import { FormError } from "@/components/form-error"
import { Button } from "@/components/ui/button"
import { Field, FieldError, FieldGroup, FieldLabel } from "@/components/ui/field"
import { GradientHeading } from "@/components/ui/gradient-heading"
import { Input } from "@/components/ui/input"
import { MenuEngineering } from "@/features/products/menu-engineering-view"
import { PreparationsManager } from "@/features/products/preparations-manager"
import { PricingInflationCard } from "@/features/products/pricing-inflation-card"
import { ProductCatalog } from "@/features/products/product-catalog"
import { RotationSchedule } from "@/features/products/rotation-schedule"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet"
import { useCreateProduct } from "@/hooks/use-products"
import { FINANCE_RANGES, rangeWindow, type FinanceRange } from "@/lib/finance-range"

const schema = z.object({
  name: z
    .string()
    .trim()
    .min(2, "Mínimo 2 caracteres")
    .max(120)
    // Evita nombres vacíos o basura: al menos una letra o número.
    .refine((v) => /[\p{L}\p{N}]/u.test(v), "Ingresá un nombre válido"),
  price: z
    .string()
    .min(1, "Ingresá un precio")
    .refine((v) => Number(v) > 0, "El precio debe ser mayor a 0"),
  category: z.string().max(60).optional(),
  // Where it's prepared — obligatorio, sin preseleccionar (evita "todo Cocina").
  station: z.enum(["KITCHEN", "BAR"], { message: "Elegí la estación" }),
})

type ProductValues = z.infer<typeof schema>

export function ProductsPage() {
  const createProduct = useCreateProduct()
  const [open, setOpen] = useState(false)
  const [serverError, setServerError] = useState<string | null>(null)
  // Selector de período único (Productos v3 Fase 1, B1): gobierna menu
  // engineering y rotación; el catálogo lo usa para "vendidos".
  const [range, setRange] = useState<FinanceRange>("month")
  const period = useMemo(() => rangeWindow(range), [range])

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ProductValues>({
    resolver: zodResolver(schema),
    defaultValues: { name: "", price: "", category: "" },
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
    <div className="mx-auto flex w-full max-w-7xl flex-col gap-5 px-4 py-6 sm:px-6 sm:py-8">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div className="flex flex-col gap-1">
          <GradientHeading size="md" weight="bold">
            Productos
          </GradientHeading>
          <p className="text-sm text-muted-foreground">Tu catálogo y precios.</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex flex-wrap items-center gap-1">
            {FINANCE_RANGES.map((r) => (
              <Button
                key={r.value}
                size="sm"
                variant={range === r.value ? "default" : "outline"}
                onClick={() => setRange(r.value)}
              >
                {r.label}
              </Button>
            ))}
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
                      aria-invalid={!!errors.station}
                      defaultValue=""
                      className="h-9 rounded-md border border-input bg-transparent px-3 text-sm shadow-xs"
                      {...register("station")}
                    >
                      <option value="" disabled>
                        Elegí estación…
                      </option>
                      <option value="KITCHEN">Cocina</option>
                      <option value="BAR">Barra</option>
                    </select>
                    <FieldError>{errors.station?.message}</FieldError>
                  </Field>
                </FieldGroup>
                <FormError message={serverError} />
                <Button type="submit" disabled={createProduct.isPending}>
                  {createProduct.isPending ? "Creando…" : "Crear producto"}
                </Button>
              </form>
            </SheetContent>
          </Sheet>
        </div>
      </header>

      {/* Menu engineering (Productos v2 Tanda A): la carta clasificada. */}
      <MenuEngineering period={period} />

      {/* Productos v2 Tanda B: precios vs inflación + rotación por día. */}
      <div className="grid gap-5 lg:grid-cols-2">
        <PricingInflationCard />
        <RotationSchedule period={period} />
      </div>

      {/* Catálogo (Productos v3 Fase 1): costo/te deja/vendidos + buscador. */}
      <ProductCatalog period={period} />

      {/* Productos v2 Tanda C: recetas madre (preparaciones base). */}
      <PreparationsManager />
    </div>
  )
}
